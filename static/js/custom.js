// Fetch the JSON data containing country names and codes
fetch('https://restcountries.com/v3.1/all')
        .then(response => response.json())
        .then(data => {
            const countrySelect = document.getElementById('countrySelect');
            data.forEach(country => {
                const option = document.createElement('option');
                option.value = country.name.common;
                option.text = country.name.common;
                countrySelect.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading countries:', error));
