from app.automation.engine import automation_engine
from app.automation.workflows import morning_briefing


def main() -> None:

    print("MONEROAI AUTOMATION TEST")
    print("Registered workflows:", automation_engine.list_workflows())
    print("Running:", morning_briefing.name)

    for result in automation_engine.run_workflow(
        morning_briefing.name
    ):
        print(result)


if __name__ == "__main__":
    main()
