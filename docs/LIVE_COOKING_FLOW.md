# GlucoPlate Live Cooking Flow

This diagram is the implementation-grounded flow for the current Live Cook Room work and its progressive enhancements.

It reflects the existing authenticated room foundation first: create or join, invite codes, participant presence, ready state, synchronized recipe steps, shared ingredient and timer state, chat, help requests, activity, public-room publishing, and leaving the room.

Video, AI assistance, substitutions, shopping, replay, and gamification extend the same room and cooking-session model. They must not introduce replacement flows, duplicate state, or competing session concepts.

```mermaid
flowchart LR
    A["Open recipe"] --> B["Enter Cook Mode"]
    B --> C{"Use Live Room?"}

    C -->|"No"| D["Private cooking session"]
    D --> D1["Step navigation"]
    D --> D2["Timers"]
    D --> D3["Ingredient checklist"]
    D --> D4["Post-cook feedback"]

    C -->|"Yes"| E{"Create or Join"}
    E -->|"Create"| F["Create authenticated room"]
    F --> F1["Attach current recipe"]
    F --> F2["Generate 6-character invite code"]
    F --> F3["Set visibility: private or public"]
    F --> F4["Host marked ready"]

    E -->|"Join"| G["Enter invite code"]
    G --> G1["Normalize and validate code"]
    G1 --> G2["Verify Firebase token"]
    G2 --> G3["Join active room"]

    F4 --> H["Waiting room"]
    G3 --> H
    H --> H1["Participant presence"]
    H --> H2["Ready / Not ready"]
    H --> H3["Copy and share invite code"]
    H --> H4["Leave room"]
    H --> I{"Host starts cooking"}

    I --> J["Active shared cooking room"]
    J --> J1["Synchronize current recipe step"]
    J --> J2["Shared ingredient checklist state"]
    J --> J3["Shared timer state"]
    J --> J4["Chat messages"]
    J --> J5["Need Help events"]
    J --> J6["Append-only activity feed"]
    J --> J7["Participant online / away status"]
    J --> J8["Room revision and polling sync"]

    J1 --> K["Existing room shell remains authoritative"]
    J2 --> K
    J3 --> K
    J4 --> K
    J5 --> K
    J6 --> K
    J7 --> K
    J8 --> K

    K --> L{"Progressive enhancements"}

    L --> M["Video and voice layer"]
    M --> M1["Provider-neutral video room"]
    M --> M2["Host video area"]
    M --> M3["Participant tiles"]
    M --> M4["Mute / camera / connection state"]

    L --> N["AI cooking assistance"]
    N --> N1["Step-aware confidence coach"]
    N --> N2["Explain technique or timing"]
    N --> N3["Never block primary cooking flow"]

    L --> O["Substitution challenge"]
    O --> O1["Missing ingredient event"]
    O1 --> O2["AI and rule-based candidates"]
    O2 --> O3["Allergy uncertainty warning"]
    O3 --> O4["Participant suggestions and votes"]
    O4 --> O5["Host confirms replacement"]
    O5 --> O6["Update recipe, checklist, activity, and history"]

    L --> P["Shopping extension"]
    P --> P1["Add one or all missing ingredients"]
    P1 --> P2["GlucoPlate shopping list"]
    P2 --> P3["Last-known price with source and date"]
    P3 --> P4["Nearby store or retailer link"]
    P4 --> P5["Connected cart only when supported"]

    L --> Q["Public activity and discovery"]
    Q --> Q1["Publish activity only for public rooms"]
    Q1 --> Q2["Keep private membership and room data protected"]

    L --> R["Session completion"]
    R --> R1["Mark recipe complete"]
    R1 --> R2["Persist decisions and substitutions"]
    R2 --> R3["Post-cook feedback"]
    R3 --> R4["Flavor Memory signals"]
    R4 --> R5["Future authenticated replay metadata"]

    R5 --> S["Recorded session history"]
    S --> S1["Private replay access"]
    S --> S2["Timeline of steps, help, substitutions, and completion"]
    S --> S3["Optional points, badges, and streaks"]

    T["Cross-cutting rules"] --> T1["Authenticated and enterprise-scoped access"]
    T --> T2["Backend-authoritative permissions and decisions"]
    T --> T3["Escape user-controlled chat and activity content"]
    T --> T4["Display degraded and failure states"]
    T --> T5["Do not guarantee allergy safety"]
    T --> T6["Do not claim live price or inventory without a reliable source"]

    T1 -.-> F
    T2 -.-> K
    T3 -.-> J4
    T4 -.-> G2
    T5 -.-> O3
    T6 -.-> P3
```

## Task-planning rule

Any task that changes Cooking Mode, live rooms, participants, ingredients, timers, chat, help, activity, substitutions, shopping, video, or replay must identify the node or transition in this flow that it implements or strengthens.

The implemented room shell remains authoritative. Enhancements must attach to the existing room and `CookingSession` direction instead of creating parallel flows.
