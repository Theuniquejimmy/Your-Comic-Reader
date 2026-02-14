# Your-Comic-Reader
Comic reader with panel detection, boder control, double click panel zoom, and more.

Core Features Implemented:

    Smart Panel Detection: Uses Computer Vision (OpenCV) to automatically detect comic panels. It filters out thin gutters, wide cinematic panels, and tiny artifacts.

    Auto-Crop: A toggle to automatically remove white/black borders from pages to maximize screen space.

    Magnifying Glass: A centered lens tool that lets you read small text at 100% resolution without zooming the whole page.

    Double-Click Zoom: Double-clicking a specific panel zooms to fill the screen with just that panel.

    Smart Navigation:

        Clicking the Art: Does nothing (prevents accidental page turns while zooming).

        Clicking the Black Background: Left side goes back, Right side goes forward.

        Spacebar: Advances to the next panel or page.

    Visual Debugging: Shows Light Green dashed lines around detected panels (only when viewing the full page) so you know where the "Smart Nav" will take you next.
