from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from ..schemas.course import CourseInput, CourseResponse, CourseOutput
from ..services.gemini import generate_course_json
import os
from urllib.parse import unquote
from ..services.pdf import generate_course_pdf
from ..db.database import get_db
from ..models.course import Course
from fastapi.responses import StreamingResponse
from ..services.gemini import VISUAL_STORE

router = APIRouter()

@router.post("/generate-course", response_model=CourseResponse)
def generate_course_endpoint(user_input: CourseInput, db: Session = Depends(get_db), request: Request = None):
    try:
        # 1. Generate content with Gemini
        course_data, fallback_info = generate_course_json(user_input)
        
        is_fallback = False
        fallback_type = None
        
        if isinstance(fallback_info, tuple):
            is_fallback = True
            is_curated, is_generic = fallback_info
            if is_curated:
                fallback_type = "curated"
            elif is_generic:
                fallback_type = "generic"
            else:
                fallback_type = "ai-plain"
        else:
            is_fallback = fallback_info

        # 2. Save to DB
        # Prepare course object and set visual_aid links before first commit so stored JSON contains links
        initial_json = course_data.model_dump()
        # Instantiate Course to get a server-side id via SQLAlchemy default
        db_course = Course(
            topic=user_input.topic,
            skill_level=user_input.skill_level,
            learning_style=user_input.learning_style,
            goal=user_input.goal,
            generated_json=initial_json
        )

        # Build absolute base from request if available, else use relative paths
        if request is not None:
            base_url = str(request.base_url).rstrip('/')
        else:
            base_url = ''

        # SQLAlchemy will assign a default id on object creation; use it to craft URLs
        course_id = db_course.id
        if not course_id:
            # if id not populated yet, we'll commit once to generate it then update below
            db.add(db_course)
            db.commit()
            db.refresh(db_course)
            course_id = db_course.id

        updated = db_course.generated_json.copy()
        modules = updated.get('modules', [])
        print(f"[routes/courses] course_id={course_id} before updating modules, modules_count={len(modules)}")

        # Ensure static visuals directory exists
        static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'visuals')
        static_dir = os.path.normpath(static_dir)
        os.makedirs(static_dir, exist_ok=True)

        def build_svg_from_topics(topics: list) -> str:
            box_w = 300
            box_h = 44
            padding = 16
            spacing = 12
            width = box_w + padding * 2
            height = max(box_h + padding * 2, len(topics) * (box_h + spacing) + padding * 2)

            def esc(t):
                return (t or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            items = []
            for i, t in enumerate(topics):
                x = padding
                y = padding + i * (box_h + spacing)
                items.append(f'<rect x="{x}" y="{y}" rx="8" ry="8" width="{box_w}" height="{box_h}" fill="#ffffff" stroke="#94a3b8" stroke-width="1.2"/>')
                text = esc(t if len(t) <= 60 else t[:57] + '...')
                items.append(f'<text x="{x+12}" y="{y + box_h/2 + 5}" font-family="Inter, Arial, sans-serif" font-size="13" fill="#0f172a">{text}</text>')
                if i > 0:
                    lx = x + box_w/2
                    y1 = y - spacing/2
                    y2 = y
                    items.append(f'<line x1="{lx}" y1="{y1}" x2="{lx}" y2="{y2}" stroke="#cbd5e1" stroke-width="2"/>')

            svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">' + ''.join(items) + '</svg>'
            return svg

        for m in modules:
            num = m.get('module_number')
            if num is None:
                continue

            topics = m.get('topics', []) or []
            try:
                svg_content = build_svg_from_topics(topics)
                filename = f"course_{course_id}_module_{num}.svg"
                file_path = os.path.join(static_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as fh:
                    fh.write(svg_content)
                m['visual_aid'] = f"/static/visuals/{filename}"
                print(f"[routes/courses] wrote visual for module {num} -> /static/visuals/{filename}")
            except Exception as e:
                print(f"Failed to build/write visual for module {num}: {e}")
                m['visual_aid'] = None
        print(f"[routes/courses] assigned updated generated_json, committing...\n")
        db_course.generated_json = updated
        db.add(db_course)
        db.commit()
        db.refresh(db_course)

        # Return stored generated JSON (which now contains /static/visuals/* URLs where applicable)
        return CourseResponse(
            status="success",
            id=db_course.id,
            course=CourseOutput(**db_course.generated_json),
            is_fallback=is_fallback,
            fallback_type=fallback_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/pdf/{course_id}")
def export_pdf(course_id: str, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    course_obj = CourseOutput(**db_course.generated_json)
    pdf_buffer = generate_course_pdf(course_obj)
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=roadmap_{course_id}.pdf"}
    )

@router.get("/recent-courses")
def get_recent_courses(limit: int = 5, db: Session = Depends(get_db)):
    courses = db.query(Course).order_by(Course.created_at.desc()).limit(limit).all()
    return [{
        "id": c.id,
        "topic": c.topic,
        "created_at": c.created_at.isoformat(),
        "course_title": c.generated_json.get("course_title", c.topic)
    } for c in courses]

@router.get("/course/{course_id}")
def get_course_details(course_id: str, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Sanitize stored JSON to remove visual_aid links for client rendering
    sanitized = db_course.generated_json.copy()
    for m in sanitized.get('modules', []):
        if 'visual_aid' in m:
            m['visual_aid'] = None

    return {
        "id": db_course.id,
        "course": sanitized,
        "topic": db_course.topic,
        "is_fallback": False
    }


@router.get("/visual/temp/{key}")
def get_temp_visual(key: str):
    svg = VISUAL_STORE.get(key)
    if not svg:
        raise HTTPException(status_code=404, detail="Visual not found or expired")
    return Response(content=svg, media_type='image/svg+xml')


@router.get("/visual/{course_id}/{module_number}")
def get_visual(course_id: str, module_number: int, db: Session = Depends(get_db)):
    db_course = db.query(Course).filter(Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    course_json = db_course.generated_json
    modules = course_json.get('modules', [])
    target = None
    for m in modules:
        if m.get('module_number') == module_number:
            target = m
            break

    if not target:
        raise HTTPException(status_code=404, detail="Module not found")

    visual = target.get('visual_aid')
    if not visual:
        raise HTTPException(status_code=404, detail="Visual aid not available for this module")

    # If visual is a data URL with SVG payload, decode and return as image/svg+xml
    if isinstance(visual, str) and visual.startswith('data:image/svg+xml'):
        try:
            _, payload = visual.split(',', 1)
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid data URL stored")
        from urllib.parse import unquote
        svg = unquote(payload)
        return Response(content=svg, media_type='image/svg+xml')

    # If it's an absolute HTTP(S) URL, proxy it
    if isinstance(visual, str) and (visual.startswith('http://') or visual.startswith('https://')):
        import requests
        try:
            r = requests.get(visual, timeout=10)
            r.raise_for_status()
            content_type = r.headers.get('Content-Type', 'image/svg+xml')
            return Response(content=r.content, media_type=content_type)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch visual: {e}")

    # If it's a relative path (starts with '/'), instruct clients to fetch from API host
    if isinstance(visual, str) and visual.startswith('/'):
        raise HTTPException(status_code=400, detail="Please fetch the visual directly from the API host using the provided relative path")

    raise HTTPException(status_code=404, detail="Visual aid could not be resolved")

