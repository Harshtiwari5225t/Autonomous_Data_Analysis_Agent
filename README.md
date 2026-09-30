# 📊 Autonomous Data Analysis Agent

An **Autonomous Data Analysis Agent** that allows users to upload a dataset and ask questions about the data using natural language. The system automatically performs **data loading, data cleaning, profiling, analysis planning, statistical analysis, and result generation**.

The project combines **Agentic AI, Google Gemini, Python, Pandas, and Streamlit** to create an interactive data-analysis system that can determine the appropriate analysis operation based on the user's query.

---

## 🚀 Project Overview

Traditional data analysis often requires users to manually inspect datasets, clean missing or duplicate records, write analysis code, and interpret the results.

The **Autonomous Data Analysis Agent** automates this workflow.

The user only needs to:

1. Upload a dataset.
2. Ask a question in natural language.
3. The agent analyzes the dataset.
4. The system automatically determines the required analysis operation.
5. The requested operation is executed on the cleaned dataset.
6. The result and a natural-language insight are returned in **JSON format**.

### Example

**User Query:**

> What is the average discounted price?

The agent can determine that the query requires an **average operation** on the `discounted_price` column and execute the analysis automatically.

---

# 🎯 Problem Statement

Analyzing large datasets manually requires knowledge of programming, statistics, data cleaning, and visualization tools.

The objective of this project is to develop an **AI-powered autonomous data analysis system** that can:

* Accept structured datasets from users.
* Automatically inspect the uploaded data.
* Clean and preprocess the dataset.
* Understand natural-language analytical questions.
* Decide which analysis operation is required.
* Execute the analysis using Python/Pandas.
* Generate meaningful insights.
* Return the final result in a structured JSON format.

The system is designed to reduce the amount of manual coding required for basic exploratory data analysis.

---

# 🧠 Agentic AI Approach

The project follows an **Agentic AI architecture**.

Instead of directly mapping every user question to a fixed function, the system uses an AI model to understand the user's request and generate an **analysis plan**.

### Agent Workflow

```text
User
  ↓
Upload Dataset
  ↓
Data Loading
  ↓
Data Profiling
  ↓
Data Cleaning
  ↓
User Natural-Language Query
  ↓
Gemini AI
  ↓
Analysis Plan
  ↓
Pandas Analysis
  ↓
Result Generation
  ↓
Insight Generation
  ↓
JSON Response
```

The AI model is responsible for understanding the user's intent, while deterministic Python/Pandas operations are used to perform the actual numerical calculations.

This separation helps prevent the language model from directly inventing numerical results.

---

# 📂 Dataset

The project currently uses the **Amazon Sales Dataset (`amazon.csv`)**, obtained from Kaggle.

### Dataset Source

**Kaggle:**
https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset

The dataset contains information about products listed on Amazon, including product details, categories, prices, discounts, ratings, and customer rating counts.

The original dataset contains approximately **1,465 product records and 16 attributes**.

For this project, the following attributes are particularly relevant:

| Attribute             | Description                                            |
| --------------------- | ------------------------------------------------------ |
| `product_id`          | Unique identifier of the product                       |
| `product_name`        | Name of the product                                    |
| `category`            | Product category and sub-category                      |
| `discounted_price`    | Price after applying the discount                      |
| `actual_price`        | Original/listed price                                  |
| `discount_percentage` | Percentage discount offered                            |
| `rating`              | Average customer rating                                |
| `rating_count`        | Number of customer ratings/reviews                     |
| `about_product`       | Description of the product                             |
| `user_id`             | Identifier associated with users who submitted reviews |

---

# ⚠️ Important Dataset Limitation

Although the dataset is commonly referred to as an **Amazon Sales Dataset**, it does **not contain actual transactional sales information**.

The dataset does not provide fields such as:

* Units sold
* Quantity sold
* Order volume
* Revenue
* Sales amount
* Transaction history

Therefore, the system **cannot determine the actual best-selling product**.

The `rating_count` field represents the number of customer ratings/reviews. It can be used as a **popularity or customer-engagement proxy**, but it must **not be interpreted as the number of products sold**.

For example:

```text
High rating_count
        ↓
Higher customer engagement/popularity
        ≠
Higher number of products sold
```

Therefore, the project focuses on **product, pricing, discount, rating, category, popularity, and data-quality analysis** rather than actual sales-volume prediction.

---

# 🔍 Scope of Analysis

The agent can perform several types of analysis on the dataset.

### 1. Product Analysis

The system can analyze individual product characteristics such as:

* Product rating
* Product price
* Discount
* Rating count
* Product popularity

Example:

```text
Which products have the highest ratings?
```

---

### 2. Price Analysis

The agent can analyze:

* Average discounted price
* Minimum price
* Maximum price
* Price distributions
* Price comparisons

Example:

```text
What is the average discounted price?
```

---

### 3. Discount Analysis

The system can analyze:

* Average discount percentage
* Maximum discount
* Minimum discount
* Discounts across categories
* Relationship between actual and discounted prices

Example:

```text
Which products have the highest discount percentage?
```

---

### 4. Rating Analysis

The system can analyze:

* Average rating
* Highest-rated products
* Lowest-rated products
* Rating distributions

Example:

```text
What is the average product rating?
```

---

### 5. Popularity Analysis

The `rating_count` attribute can be used to identify products receiving a large number of customer ratings.

Example:

```text
Which products have the highest rating count?
```

This represents **customer engagement/popularity**, not actual sales.

---

### 6. Category Analysis

The system can analyze:

* Number of products per category
* Average price by category
* Average rating by category
* Average discount by category
* Category-level statistics

Example:

```text
Which category has the highest average discount?
```

---

### 7. Data Quality Analysis

The system automatically checks for:

* Missing values
* Duplicate rows
* Column inconsistencies
* Data types
* Number of unique values
* Dataset dimensions

---

# 🧹 Data Cleaning

Before performing analysis, the dataset passes through an automated data-cleaning stage.

The cleaning module performs operations such as:

### Duplicate Removal

Duplicate records are identified and removed.

```text
Original Dataset
      ↓
Find Duplicate Rows
      ↓
Remove Duplicates
      ↓
Clean Dataset
```

### Missing Value Handling

Missing numerical values can be replaced using appropriate statistical values such as the median.

Categorical missing values can be handled using the mode or an `"Unknown"` value when appropriate.

### Column Cleaning

Column names are normalized by removing unnecessary spaces.

### Data Profiling

The system generates information about:

* Number of rows
* Number of columns
* Column names
* Data types
* Missing values
* Duplicate records

---

# 🏗️ Modular Architecture

The project follows a modular architecture so that each component has a specific responsibility.

```text
                 ┌─────────────────────┐
                 │        User         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Streamlit UI     │
                 │      main.py        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    Orchestrator     │
                 │   orchestrator.py   │
                 └──────────┬──────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       ┌───────────┐  ┌────────────┐  ┌─────────────┐
       │   Load    │  │   Profile  │  │    Clean    │
       │   Data    │  │    Data    │  │    Data     │
       └───────────┘  └────────────┘  └─────────────┘
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                 ┌─────────────────────┐
                 │    Google Gemini    │
                 │   Analysis Planner  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Analysis Plan     │
                 │      JSON           │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Pandas Analysis    │
                 │  Deterministic Ops  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Insight Generation │
                 │    Gemini + Data    │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    JSON Response    │
                 └─────────────────────┘
```

---

# 📦 Project Modules

The project is divided into separate modules.

## `main.py`

`main.py` acts as the **frontend layer** of the application.

Responsibilities:

* Launch Streamlit application
* Provide dataset upload interface
* Accept CSV, Excel and JSON files
* Accept natural-language questions
* Display analysis results
* Display JSON output
* Provide JSON download functionality

---

## `orchestrator.py`

`orchestrator.py` is the **core agent/controller module**.

It coordinates the complete workflow.

Responsibilities:

* Load the dataset
* Profile the dataset
* Trigger data cleaning
* Understand the user's query
* Communicate with Gemini
* Generate an analysis plan
* Execute the required analysis
* Generate insights
* Construct the final JSON response

The orchestrator acts as the central decision-making component of the application.

---

## `helper.py`

`helper.py` contains reusable data-processing functions.

Responsibilities include:

* Dataset loading
* Data profiling
* Data cleaning
* Statistical calculations
* Column information extraction

This keeps the data-processing logic separate from the application and orchestration logic.

---

# 🤖 Google Gemini Integration

Google Gemini is used as the natural-language reasoning component of the system.

The model helps transform a user's natural-language question into a structured analysis plan.

### Example

User asks:

```text
What is the average rating?
```

Gemini generates an analysis plan similar to:

```json
{
    "operation": "average",
    "column": "rating"
}
```

The Python application then executes the operation using Pandas.

```text
Natural Language
       ↓
Gemini
       ↓
Structured Analysis Plan
       ↓
Pandas
       ↓
Numerical Result
```

This approach allows the AI model to interpret the query while Python performs the actual calculation.

---

# 🐼 Pandas Analysis Engine

Pandas is used as the primary data-processing and analysis library.

Depending on the generated analysis plan, the system can perform operations such as:

* Average
* Sum
* Minimum
* Maximum
* Count
* Descriptive statistics
* Category-based analysis
* Column-level analysis

Example:

```python
df["rating"].mean()
```

The result is then passed to the output-generation stage.

---

# 📤 JSON Output

The final result of the agent is returned in structured JSON format.

Example:

```json
{
    "status": "success",
    "question": "What is the average rating?",
    "analysis": {
        "operation": "average",
        "column": "rating",
        "result": 4.09
    },
    "insight": "The dataset has an average product rating of approximately 4.09."
}
```

A structured JSON response makes the system easier to integrate with:

* Web applications
* APIs
* Dashboards
* Other AI agents
* Data-processing systems

---

# 🔄 Complete System Workflow

The complete execution process is:

```text
1. User uploads dataset
          ↓
2. Dataset is saved
          ↓
3. Dataset is loaded
          ↓
4. Dataset is profiled
          ↓
5. Data cleaning is performed
          ↓
6. User enters natural-language query
          ↓
7. Query is sent to Gemini
          ↓
8. Gemini generates analysis plan
          ↓
9. Analysis plan is validated
          ↓
10. Pandas performs analysis
          ↓
11. Gemini generates an insight
          ↓
12. Final response is converted to JSON
          ↓
13. JSON displayed to user
```

---

# 📁 Project Structure

```text
Autonomous_Data_Analysis_Agent/
│
├── main.py
├── orchestrator.py
├── helper.py
├── requirements.txt
├── .env
├── .gitignore
│
├── data/
│   └── uploads/
│
└── README.md
```

### File Description

| File/Folder        | Purpose                                                   |
| ------------------ | --------------------------------------------------------- |
| `main.py`          | Streamlit user interface                                  |
| `orchestrator.py`  | Agent orchestration and workflow                          |
| `helper.py`        | Data loading, cleaning and analysis utilities             |
| `requirements.txt` | Python dependencies                                       |
| `.env`             | API key configuration                                     |
| `.gitignore`       | Prevents sensitive/unnecessary files from being committed |
| `data/uploads/`    | Stores uploaded datasets                                  |
| `README.md`        | Project documentation                                     |

---

# 🛠️ Technologies Used

### Programming Language

* **Python**

### AI Model

* **Google Gemini**

### Data Processing

* **Pandas**
* **NumPy**

### Frontend

* **Streamlit**

### Environment Management

* **Python Virtual Environment (`venv`)**
* **python-dotenv**

### File Formats

* CSV
* Excel
* JSON

---

# 📋 Prerequisites

Before running the project, install:

* Python 3.x
* pip
* Git
* VS Code or another Python IDE
* Google Gemini API key

---

# ⚙️ Installation

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Navigate to the project directory:

```bash
cd Autonomous_Data_Analysis_Agent
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

---

# 📦 Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

If the requirements file is not available, install the main dependencies:

```bash
pip install streamlit pandas numpy openpyxl python-dotenv google-genai
```

---

# 🔑 Gemini API Configuration

Create a `.env` file in the project root directory:

```text
GEMINI_API_KEY=your_gemini_api_key_here
```

The `.env` file should be located here:

```text
Autonomous_Data_Analysis_Agent/
│
├── .env
├── main.py
├── orchestrator.py
└── helper.py
```

### Important

Do not upload your API key to GitHub.

Add the following to `.gitignore`:

```text
.env
venv/
__pycache__/
*.pyc
data/uploads/
```

---

# ▶️ Running the Application

Do not run the Streamlit application using:

```bash
python main.py
```

Instead, start it using:

```bash
streamlit run main.py
```

Streamlit will provide a local URL, usually similar to:

```text
http://localhost:8501
```

Open the URL in your browser.

---

# 📊 Using the Application

### Step 1 — Upload Dataset

Upload a supported dataset:

```text
.csv
.xlsx
.xls
.json
```

### Step 2 — Enter a Question

For example:

```text
What is the average rating?
```

or:

```text
Which product has the highest discount?
```

or:

```text
What is the maximum discounted price?
```

### Step 3 — Analyze

Click:

```text
Analyze Data
```

### Step 4 — View Result

The agent displays the analysis result and generated insight in JSON format.

---

# 💬 Example Queries

The system can handle questions such as:

```text
What is the average rating?
```

```text
What is the average discounted price?
```

```text
What is the maximum discount percentage?
```

```text
Which product has the highest rating?
```

```text
Which product has the highest rating count?
```

```text
How many products are present in the dataset?
```

```text
What are the basic statistics of the dataset?
```

```text
Which category contains the most products?
```

```text
What is the minimum actual price?
```

```text
What is the maximum discounted price?
```

---

# 🧩 Modular Design

The project uses a modular architecture instead of placing all functionality inside a single Python file.

### Layer 1 — Presentation Layer

```text
main.py
```

Responsible for user interaction.

### Layer 2 — Agent/Orchestration Layer

```text
orchestrator.py
```

Responsible for coordinating the AI-driven workflow.

### Layer 3 — Data Processing Layer

```text
helper.py
```

Responsible for loading, cleaning and profiling data.

### Layer 4 — AI Reasoning Layer

```text
Google Gemini
```

Responsible for understanding natural-language questions and generating analysis plans/insights.

### Layer 5 — Computation Layer

```text
Pandas
```

Responsible for deterministic data calculations.

### Layer 6 — Output Layer

```text
JSON
```

Responsible for providing structured results.

---

# 🔐 Security Considerations

The project uses an API key to communicate with Google Gemini.

The API key should:

* Be stored in `.env`
* Never be hard-coded into Python files
* Never be committed to GitHub
* Never be included in screenshots or public documentation

The `.env` file should always be included in `.gitignore`.

---

# ⚡ Key Features

* 🤖 Agentic AI-based analysis
* 📂 CSV, Excel and JSON support
* 🧹 Automated data cleaning
* 🔍 Automatic data profiling
* 💬 Natural-language queries
* 🧠 Gemini-powered analysis planning
* 🐼 Pandas-based deterministic calculations
* 📊 Product and category analysis
* 💰 Price and discount analysis
* ⭐ Rating analysis
* 📈 Popularity/engagement analysis
* 📋 Structured JSON output
* 🌐 Streamlit web interface
* 📥 JSON result download

---

# 🔮 Future Enhancements

The project can be extended with additional capabilities such as:

* Interactive data visualizations
* Automatic chart generation
* More advanced statistical analysis
* Correlation analysis
* Outlier detection
* Trend analysis
* Regression analysis
* Natural-language data visualization
* SQL database support
* Multiple datasets
* RAG-based dataset documentation
* Automated report generation
* Multi-agent architecture
* Conversation memory
* Voice-based data queries
* Deployment using cloud platforms
* Support for larger datasets

---

# 📌 Current Limitations

1. The current Amazon dataset does not contain actual sales volume or units-sold information.
2. `rating_count` is treated as a popularity/engagement indicator rather than sales.
3. The current analysis operations are primarily statistical and tabular.
4. The system depends on the availability of the Gemini API for AI-based query interpretation.
5. Very large datasets may require additional optimization.
6. Data-cleaning decisions are currently based on predefined preprocessing rules.

---

# 📚 Dataset Reference

**Karkavelraja J. — Amazon Sales Dataset**

Kaggle:

https://www.kaggle.com/datasets/karkavelrajaj/amazon-sales-dataset

---

# 👨‍💻 Project

**Project Name:** Autonomous Data Analysis Agent

**Domain:** Agentic AI / Data Analytics / Generative AI

**Frontend:** Streamlit

**Programming Language:** Python

**AI Model:** Google Gemini

**Data Processing:** Pandas & NumPy

**Output Format:** JSON

---

# ⭐ Conclusion

The **Autonomous Data Analysis Agent** provides an AI-assisted approach to exploratory data analysis. By combining **Google Gemini for natural-language understanding and analysis planning** with **Pandas for deterministic data processing**, the system allows users to interact with structured datasets using ordinary questions rather than manually writing analysis code.

The modular architecture makes the system easier to maintain, extend, and integrate with additional datasets, analytical operations, AI models, and interfaces in the future.
