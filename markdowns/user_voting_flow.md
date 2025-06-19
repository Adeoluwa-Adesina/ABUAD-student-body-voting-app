```mermaid
flowchart TD
    subgraph "Authentication"
        A[<i class='fa fa-user-lock'></i> Start: User Logs In]
    end

    subgraph "Voting Process"
        B[<i class='fa fa-list-ul'></i> User navigates to /polls page]
        C{<i class='fa fa-mouse-pointer'></i> User selects a poll}
        D{<i class='fa fa-question-circle'></i> Already Voted?}
        E[<i class='fa fa-check-circle'></i> Display vote options]
        F[<i class='fa fa-paper-plane'></i> User selects an option and clicks Submit]
        G[<i class='fa fa-database'></i> Server records vote in Database]
        H[<i class='fa fa-chart-bar'></i> Redirect to Results Page]
    end

    subgraph "Alternative Flow"
        I[<i class='fa fa-info-circle'></i> Display 'Already Voted' message]
    end

    subgraph "End Points"
        End1[<i class='fa fa-flag-checkered'></i> End]
        End2[<i class='fa fa-flag-checkered'></i> End]
    end

    %% --- Flow Connections ---
    A --> B
    B --> C
    C --> D
    D -- "No" --> E
    D -- "Yes" --> I
    E --> F
    F --> G
    G --> H
    H --> End1
    I --> End2
    
    %% --- Styling ---
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#333
    classDef process fill:#e3f2fd,stroke:#1e88e5,color:#1565c0
    classDef decision fill:#fff3e0,stroke:#fb8c00,color:#e65100
    classDef altflow fill:#fce4ec,stroke:#d81b60,color:#880e4f
    classDef db_interaction fill:#e0f2f1,stroke:#00897b,color:#004d40
    classDef endpoint fill:#eceff1,stroke:#546e7a,color:#263238

    class A,B,C,E,F,H process
    class G db_interaction
    class D decision
    class I altflow
    class End1,End2 endpoint
```

<!-- *Note: For the icons (`<i class='fa fa-user-lock'></i>`) to render correctly in VS Code's preview, you may need to have an extension that supports Font Awesome icons within Mermaid diagrams. The diagram will still work and be perfectly readable without the icons.* -->
