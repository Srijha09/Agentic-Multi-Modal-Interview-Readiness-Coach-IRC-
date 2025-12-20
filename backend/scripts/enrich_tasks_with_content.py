"""
Script to enrich existing tasks with study materials and resources.
This updates tasks that don't have content populated.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.database import SessionLocal
from app.db.models import DailyTask
from app.services.planner import StudyPlanner

# Fix Windows encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def enrich_tasks():
    """Enrich all tasks without content."""
    db = SessionLocal()
    planner = StudyPlanner()
    
    try:
        # Get all tasks that have empty or missing content
        tasks = db.query(DailyTask).filter(
            (DailyTask.content == {}) | (DailyTask.content == None)
        ).all()
        
        if not tasks:
            print("No tasks need enrichment. All tasks already have content.")
            return
        
        print(f"Found {len(tasks)} tasks to enrich...")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Enriching task: {task.title}")
            
            try:
                # Generate content for this task
                content = planner._generate_task_content(
                    title=task.title,
                    description=task.description,
                    skill_names=task.skill_names if task.skill_names else [],
                    task_type=task.task_type.value
                )
                
                # Update task
                task.content = content
                db.commit()
                
                print(f"  ✓ Added {len(content.get('study_materials', []))} study materials")
                print(f"  ✓ Added {len(content.get('resources', []))} resources")
                print(f"  ✓ Added {len(content.get('key_concepts', []))} key concepts")
                
            except Exception as e:
                print(f"  ✗ Error enriching task {task.id}: {e}")
                db.rollback()
                continue
        
        print(f"\n✓ Successfully enriched {len(tasks)} tasks!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    enrich_tasks()


