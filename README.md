# Mock Finance

## Table of Contents

1. <a href="#description">Description</a>
2. <a href="#installation">Installation</a>
3. <a href="#code">Code Discussion</a>
4. <a href="#questions">Issues and Questions</a>
<hr><h3 id='description'>Description</h3>
Finance app for mock stock transactions. Uses Flask and Python for routing, and SQL to track user transactions. Users start with a (fake) cash balance of $10,000. Users have options to get stock quotes, buy and sell stock, or add more cash to their account.

![image](https://user-images.githubusercontent.com/64618290/101973204-14f6bd00-3beb-11eb-940f-d36a7680129a.png)

<h3 id='installation'>Installation</h3>
Flask and Python must be installed. The app may be run by navigating to the program folder and using the command 'flask run' in a terminal. Be sure to set the API key for the stock lookup website, iexcloud.io. The API key may be set in the terminal. Alternatively, it may be set by creating a .env file containing the text 'API_KEY=yourKeyHere'. This latter method requires the 'python-dotenv' package to be installed from pip. Once the program is started, it may be navigated to in a browser at 'localhost:5000'.

<h3 id='code'>Code Discussion</h3>
Some functions were provided - authentication functions, stock quote lookup, usd formatting, and basic styling and sitemap. The main body of SQL programming and route programming was provided by the current author. SQL functions are performed by utilizing the SQLAlchemy ORM. Python, with the Flask module, provides routing functionality. HTML/CSS provide the frontend to the browser, and are coded with the help of the Jinja templating engine and the Bootstrap CSS library. 

<h3 id='questions'>Issues and Questions</h3>
Issues and questions may be emailed to 'kmillergit' at the domain 'outlook.com'. The author's GitHub profile may be found at https://github.com/Koldenblue.<p><sub><sup>This readme was generated with the help of the readme generator program at https://github.com/Koldenblue/readme-generator.</sup></sub></p>