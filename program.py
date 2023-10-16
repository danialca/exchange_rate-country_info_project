from flask import Flask, render_template, request #incoming HTTP requests
from datetime import datetime
import requests  #outbound HTTP requests.

app = Flask(__name__)

# Function to fetch exchange rate data
def get_exchange_rates(base_currency):
    url = f'https://open.er-api.com/v6/latest/{base_currency}'
    response = requests.get(url)
    data = response.json()
    return data['rates']

def get_country_info(currency_code, country_data):
    for country in country_data:
        currencies = country.get('currencies', [])
        if currency_code in currencies:
            common_name = country.get('name', {}).get('common', 'N/A')
            capital = country.get('capital', ['N/A'])[0]
            return common_name, capital
    return 'N/A', 'N/A'

def convert_currencies(base_currency, amount_to_convert, *target_currencies, country_data=None):
    try:
        if country_data is None:
            raise ValueError("Country data is required for currency lookup.")
        
        # Get exchange rates for the specified base currency
        exchange_rates = get_exchange_rates(base_currency)
        
        results = []  # Store conversion results
        
        for target_currency in target_currencies:
            target_currency = target_currency.upper()
            if target_currency in exchange_rates:
                rate = exchange_rates[target_currency]
                converted_amount = amount_to_convert * rate
                
                # Get base currency info
                base_currency_info = get_country_info(base_currency, country_data)
                
                # Get target currency info
                target_currency_info = get_country_info(target_currency, country_data)
                
                results.append((amount_to_convert, base_currency, converted_amount, target_currency, target_currency_info, base_currency_info))
            else:
                results.append((None, base_currency, None, target_currency, None, base_currency_info))
        
        return results
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"



@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/currency list')
def about():
    # List all currency codes in organized chunks
    currency_codes = list(get_exchange_rates('USD').keys())
    chunk_size = 10
    chunks = [currency_codes[i:i + chunk_size] 
    for i in range(0, len(currency_codes), chunk_size)]
    
    return render_template('list.html', currency_codes=chunks)

@app.route('/convert', methods=['POST'])
def currency_conversion():
    try:
        base_currency = request.form.get('base_currency')
        base_currency = base_currency.upper()
        amount_to_convert = float(request.form.get('amount_to_convert'))
        target_currencies = request.form.getlist('target_currency')
        
        # Get the current date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Fetch country data here (similar to your existing code)
        country_api_url = 'https://restcountries.com/v3.1/all'
        response = requests.get(country_api_url)
        if response.status_code == 200:
            country_data = response.json()
            
            # Call the convert_currencies function to get the results
            results = convert_currencies(base_currency, amount_to_convert, *target_currencies, country_data=country_data)

            # Render the results in a template
            return render_template(
                'result.html',
                results=results,
                current_time=current_time
            )
        else:
            return f"Error: Unable to fetch country data. Status code: {response.status_code}"

    except ValueError:
        return "Invalid input. Please enter a valid numeric amount."

if __name__ == '__main__':
    app.run(debug=True)
