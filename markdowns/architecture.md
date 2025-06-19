```mermaid
graph TD
    subgraph "User's Device"
        direction LR
        User["<i class='fa fa-user'></i> User"] --> Browser["<i class='fa fa-window-maximize'></i> Web Browser"]
    end

    subgraph "Vercel Platform"
        direction LR
        Edge[Vercel Edge Network]

        subgraph "Compute Layer"
            Flask["<i class='fab fa-python'></i> Flask App<br>(Serverless Function)"]
        end
        
        subgraph "Storage Layer"
            Static["<i class='fa fa-folder-open'></i> Static Assets<br>(CSS, JS, Logos)"]
        end
    end

    subgraph "Database Provider"
        Supabase["<i class='fa fa-database'></i> Supabase<br>(PostgreSQL DB)"]
    end

    %% --- Data Flow ---
    Browser -- "HTTPS Request" --> Edge
    Edge -- "Route: /static/*" --> Static
    Edge -- "Route: /..." --> Flask
    Flask -- "SQL Query (psycopg2)" --> Supabase
    Supabase -- "DB Response" --> Flask
    Flask -- "HTML/API Response" --> Edge
    Edge -- "HTTPS Response" --> Browser
    
    %% --- Styling ---
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#333
    classDef user fill:#e3f2fd,stroke:#1e88e5,color:#1565c0
    classDef platform fill:#eceff1,stroke:#546e7a,color:#263238
    classDef db fill:#e0f2f1,stroke:#00897b,color:#004d40
    classDef compute fill:#fff3e0,stroke:#fb8c00,color:#e65100

    class User,Browser user
    class Edge,Static platform
    class Flask compute
    class Supabase db
```

<!-- *Note: For the icons (`<i class='fa fa-user'></i>`) to render correctly in VS Code's preview, you may need to have an extension that supports Font Awesome icons within Mermaid diagrams. The diagram will still work and be perfectly readable without the icons.* -->
