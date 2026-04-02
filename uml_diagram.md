# PawPal+ UML Class Diagram

Paste the Mermaid code below into [Mermaid Live Editor](https://mermaid.live) to render and export as `uml_final.png`.

```mermaid
classDiagram
    class Task {
        +str description
        +str scheduled_time
        +int duration_minutes
        +str priority
        +str frequency
        +str pet_name
        +bool is_complete
        +date due_date
        +mark_complete() Task
        +to_dict() dict
        +from_dict(data: dict) Task
    }

    class Pet {
        +str name
        +str species
        +date date_of_birth
        +List~Task~ tasks
        +add_task(task: Task) None
        +get_tasks() List~Task~
        +to_dict() dict
        +from_dict(data: dict) Pet
    }

    class Owner {
        +str name
        +List~Pet~ pets
        +List~str~ blocked_times
        +add_pet(pet: Pet) None
        +block_time(time_str: str) None
        +get_all_tasks() List~Task~
        +to_dict() dict
        +from_dict(data: dict) Owner
        +save_to_json(filepath: str) None
        +load_from_json(filepath: str) Owner
    }

    class Scheduler {
        +Owner owner
        +get_todays_tasks() List~Task~
        +sort_by_time(tasks) List~Task~
        +filter_tasks(tasks, pet_name, completed) List~Task~
        +detect_conflicts(tasks) List~str~
        +mark_task_complete(task: Task) None
        +generate_schedule() dict
    }

    Owner "1" --> "0..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler "1" --> "1" Owner : reads from
```
