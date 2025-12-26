# lib/open_library_api.py
import requests # type: ignore
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy # type: ignore

# --- DATABASE SETUP ---
app = Flask(__name__)
# This creates a local file 'history.db' in your project folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define what the database table looks like
class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    author = db.Column(db.String)
    year = db.Column(db.String)

# Initialize the database file
with app.app_context():
    db.create_all()

# --- API LOGIC ---
class Search:

    def get_user_search_results(self, search_term):
        # Format the search term for the URL (replace spaces with +)
        search_term_formatted = search_term.replace(" ", "+")
        
        # Define the fields we want to retrieve
        fields = ["title", "author_name", "first_publish_year"]
        fields_formatted = ",".join(fields)
        limit = 5

        URL = f"https://openlibrary.org/search.json?title={search_term_formatted}&fields={fields_formatted}&limit={limit}"

        try:
            response = requests.get(URL)
            
            # Check if the API request was successful
            if response.status_code == 200:
                data = response.json()
                docs = data.get('docs', [])

                if docs:
                    results_list = []
                    
                    # Use app_context to allow database interaction
                    with app.app_context():
                        for index, book in enumerate(docs, start=1):
                            # Extract data safely using .get()
                            title = book.get('title', 'Unknown Title')
                            authors = book.get('author_name', ['Unknown Author'])
                            author = authors[0]
                            year = str(book.get('first_publish_year', 'Year Unknown'))

                            # 1. Format for terminal display
                            results_list.append(f"{index}. {title} ({year}) by {author}")

                            # 2. Save to Database
                            new_entry = SearchHistory(title=title, author=author, year=year)
                            db.session.add(new_entry)
                        
                        # Save all changes to history.db
                        db.session.commit()
                    
                    return "\n".join(results_list)
                else:
                    return "No books found for that search term."
            else:
                return f"Error: Received status code {response.status_code} from server."
        
        except Exception as e:
            return f"An error occurred: {e}"

# --- EXECUTION ---
if __name__ == "__main__":
    choice = input("Enter 's' to Search or 'v' to View History: ").lower()
    
    if choice == 's':
        search_term = input("Enter a book title: ")
        result = Search().get_user_search_results(search_term)
        print("\n" + result)
    elif choice == 'v':
        view_history() # type: ignore
    else:
        print("Invalid choice.")