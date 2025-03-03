# Highest Grossing Films Visualization

A modern web application that visualizes data about the highest-grossing films of all time. This project presents film information in an interactive and visually appealing way.

## Features

- **Visual Data Representation**: Interactive bar charts showing the top films by box office earnings
- **Responsive Grid Layout**: Film cards displaying key information in a modern, responsive grid
- **Advanced Filtering**: Filter films by release year and country of origin
- **Dynamic Sorting**: Sort films by box office earnings, release year, or title
- **Search Functionality**: Find specific films or directors quickly
- **Pagination**: Navigate through large datasets with ease

## Technologies Used

- **HTML5**: Semantic markup and modern page structure
- **CSS3**: Modern styling with flexbox, grid, and CSS variables
- **JavaScript**: Dynamic data manipulation, filtering, and visualization
- **JSON**: Data storage and retrieval using JavaScript's fetch API

## Project Structure

```
highest-grossing-films/
├── index.html       # Main HTML file with page structure
├── css/
│   └── styles.css   # CSS styles for visual presentation
├── js/
│   └── script.js    # JavaScript for functionality and interactivity
├── data/
│   └── films.json   # JSON data containing film information
└── README.md        # Project documentation
```

## How to Use

1. **Browse Films**: Scroll through the grid of film cards to view basic information
2. **View Details**: Click on any film card to see detailed information in the details section
3. **Filter Content**: Use the year and country dropdown filters to narrow down results
4. **Search**: Enter keywords in the search box to find specific films or directors
5. **Sort Results**: Select different sorting options to reorder the film display
6. **Navigate Pages**: Use the pagination controls to move through multiple pages of results

## Data Structure

Each film record contains the following information:
- Title
- Release Year
- Director
- Box Office Earnings
- Country of Origin

## GitHub Pages Deployment

To deploy this project on GitHub Pages:

1. **Repository Creation**:
   - Create a new repository on GitHub (e.g., highest-grossing-films)
   - Clone the repository to your local machine

2. **Add Files**:
   - Add all project files to the repository
   - Commit the changes with a descriptive message
   - Push the changes to GitHub

3. **Enable GitHub Pages**:
   - Go to your repository's Settings
   - Scroll down to the GitHub Pages section
   - Under Source, select the branch you want to deploy (typically main)
   - Choose the root folder
   - Click Save

4. **Verify**:
   - GitHub will provide a URL (e.g., https://yourusername.github.io/highest-grossing-films)
   - Open the provided URL in your browser to ensure your page is live

## Local Development

To run this project locally:

1. Clone the repository to your local machine
2. Open the project folder in your code editor
3. To view the project, you can:
   - Use a local web server (recommended for full functionality)
   - Open the index.html file directly in a browser (may have limitations with fetch API)

## Credits

- Film data sourced from Wikipedia's "List of highest-grossing films"
- Icons provided by Font Awesome
- Developed as part of a web development assignment

## License

This project is available for educational purposes. Please provide attribution if you use or modify this code.
