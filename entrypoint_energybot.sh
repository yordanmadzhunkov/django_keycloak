#!/bin/sh

# Update prices
python manage.py update_rates

# Start Energy bot to scripe prices
python scripers/energy_prices.py
