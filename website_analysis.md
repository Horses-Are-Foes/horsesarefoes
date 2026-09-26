# Horses Are Foes Website Analysis

## Repository Overview
The "Horses Are Foes" website is a static HTML/CSS/JavaScript site with a 1998 Tripod aesthetic. It contains a collection of pages with various themes, including mission reports, wiki content, and interactive elements.

## Directory Structure
```
horsesarefoes/
├── CNAME
├── README.md
├── index.html
├── style.css
├── age-gate.css
├── age-gate.js
├── gifs.css
├── gifs.js
├── js/counter.js
├── robots.txt
├── sitemap.xml
├── assets/           # Contains animated GIFs and images
├── contact/          # Contact page
├── dance-the-horses-away/  # Special page with interactive elements
├── mission/         # Mission report page with large image
├── reports/         # Multiple themed report sections
└── wiki/            # Wiki content
```

## Main Pages

### index.html
- Main landing page with 1998 Tripod aesthetic
- Uses table-based layout
- Implements age gate functionality using localStorage
- Contains embedded JavaScript for age gate logic
- Features a visitor counter that starts at 6000

### contact/index.html
- Contact information page

### dance-the-horses-away/index.html
- Dedicated page for the "Dance the Horses Away" interactive element
- Contains special handling for the DANCETHEHORSESAWAY.gif

### mission/index.html
- Mission report page with large horse encounter image

### wiki/index.html
- Wiki content page

## Key Features

### Age Gate System
- Implemented in `age-gate.js` and styled with `age-gate.css`
- Uses localStorage and sessionStorage to persist user age acceptance
- Displays a psychic barrier overlay with age verification

### Visitor Counter
- Implemented in `js/counter.js`
- Starts at 6000 and increments per browser visit
- Uses localStorage to track visits
- Displays counter in multiple places using data attributes and classes

### Animated GIFs
- Managed by `gifs.js` and styled with `gifs.css`
- 15 unique GIF assets referenced
- 16 positioning rules defined in CSS
- Interactive elements:
  - DANCETHEHORSESAWAY.gif links to dedicated page
  - PROADAMERICAN.gif opens random Israel-related links
- Mobile-responsive with hiding at 700px width
- Positioned with absolute coordinates and media queries

### CSS Styling
- `style.css` defines a classic 90s web aesthetic
- Features marquee bar, sidebar, and card components
- Uses retro color schemes and typography
- Responsive design considerations

## Technical Details

### File Types
- HTML: Main pages (index.html, contact/index.html, etc.)
- CSS: Styling (style.css, age-gate.css, gifs.css)
- JavaScript: Interactivity (age-gate.js, gifs.js, js/counter.js)

### Assets
- 15+ animated GIFs in the assets/ directory
- Large image in mission/ directory (HORSEENCOUNTERPREVIEW.jpg)
- Various image formats including webp and jpg

### JavaScript Functionality
- Age gate validation using localStorage
- Visitor counter implementation
- Dynamic GIF management with click handlers
- Conditional rendering based on current page path
- Mobile responsiveness handling

## Reports Section
The reports directory contains multiple themed report sections:
- 21-million-views-tree-to-fall/
- faerie-lights-swamp-gas/
- the-dust/
- the-world-has-lied-to-you/
- top-5-underground-horse-cities/

Each contains thematic content with images and HTML pages.

## Additional Files
- `robots.txt`: Standard robot exclusion rules
- `sitemap.xml`: Site map
- `CNAME`: DNS configuration for custom domain

## Notes
1. The site uses a retro 1998 Tripod aesthetic with classic web design elements
2. The visitor counter starts at 6000 and increments per browser visit
3. The age gate system uses localStorage for persistence
4. The animated GIF system is highly interactive with special behaviors for certain GIFs
5. The site has multiple themed report sections with unique content
6. All pages maintain consistent styling and structure