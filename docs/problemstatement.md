# Problem Statement: AI-Powered Restaurant Recommendation System (Zomato Use Case)

Build an intelligent restaurant recommendation application inspired by Zomato.  
The system should combine structured restaurant data with a Large Language Model (LLM) to generate personalized, relevant, and easy-to-understand suggestions.

## Objective

Design and implement an application that:
- Collects user preferences (location, budget, cuisine, rating, and optional constraints)
- Uses a real-world restaurant dataset
- Applies LLM reasoning to rank and explain recommendations
- Presents concise, actionable results in a user-friendly format

## Scope and Workflow

### 1) Data Ingestion and Preparation
- Load and preprocess the Zomato dataset from Hugging Face:  
  [https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- Extract and normalize relevant fields such as:
  - Restaurant name
  - Location
  - Cuisine
  - Estimated cost
  - Rating
  - Other useful attributes (if available)

### 2) User Preference Collection
Capture user inputs such as:
- Location (e.g., Delhi, Bangalore)
- Budget (low, medium, high)
- Preferred cuisine (e.g., Italian, Chinese)
- Minimum acceptable rating
- Additional preferences (e.g., family-friendly, fast service)

### 3) Filtering and LLM Integration
- Filter candidate restaurants based on structured criteria
- Construct a prompt with filtered data and user preferences
- Use the LLM to:
  - Rank the best options
  - Provide short explanations for each recommendation
  - Optionally summarize trade-offs across options

### 4) Recommendation Output
Display top recommendations in a clear format, including:
- Restaurant name
- Cuisine
- Rating
- Estimated cost
- AI-generated explanation of fit

## Expected Outcome

The final system should provide high-quality, personalized restaurant recommendations that are:
- Relevant to user intent
- Transparent in reasoning
- Easy for users to compare and act on