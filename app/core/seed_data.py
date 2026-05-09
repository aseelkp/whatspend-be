from app.models.category import Category
from app.core.database import SessionLocal

DEFAULT_CATEGORIES = [
    {
        "name": "groceries",
        "display_name": "Groceries & Food",
        "description": "Expenses related to groceries and dining.",
        "color": "#4CAF50",
        "icon": "🥗",
        "is_default": True,
    },
    {
        "name": "transportation",
        "display_name": "Transportation",
        "description": "Expenses related to transportation, including public transit and fuel.",
        "color": "#2196F3",
        "icon": "🚗",
        "is_default": True,
    },
    {
        "name": "entertainment",
        "display_name": "Entertainment",
        "description": "Expenses related to entertainment, including movies, concerts, and events.",
        "color": "#FF9800",
        "icon": "🎉",
        "is_default": True,
    },
    {
        "name": "healthcare",
        "display_name": "Healthcare",
        "description": "Expenses related to healthcare, including medical bills and insurance.",
        "color": "#E91E63",
        "icon": "🏥",
        "is_default": True,
    },
    {
        "name": "other",
        "display_name": "Other",
        "description": "Miscellaneous expenses that don't fit into other categories.",
        "color": "#9E9E9E",
        "icon": "🗂️",
        "is_default": True,
    },
]

def seed_categories():
    '''Seeds the database with default categories.'''
    db = SessionLocal()

    try:
        for category in DEFAULT_CATEGORIES:
            existing = db.query(Category).filter_by(name=category["name"]).first()

            if not existing:
                category_obj = Category(**category)
                db.add(category_obj)
        db.commit()
        print("Default categories seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding categories: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()