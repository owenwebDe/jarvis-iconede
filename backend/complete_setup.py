from core.database import SETUP_WIZARD_STEPS, SetupWizardStep, get_db_session

def complete_setup():
    db = get_db_session()
    try:
        for name in SETUP_WIZARD_STEPS:
            row = db.query(SetupWizardStep).filter_by(step_name=name).one_or_none()
            if not row:
                row = SetupWizardStep(step_name=name)
                db.add(row)
            row.completed = True
            row.skipped = False
        db.commit()
        print("Setup wizard steps successfully marked completed in jarvis.db.")
    finally:
        db.close()

if __name__ == "__main__":
    complete_setup()
