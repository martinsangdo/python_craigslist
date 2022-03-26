# python_craigslist
Parse entire website to find out part time jobs
1. homepage: https://craigslist.org/?lang=en&cc=us
2. get regions: africa, asia, ...
3. go into each country: https://www.craigslist.org/about/sites#US
4. each state, city: https://losangeles.craigslist.org/
5. jobs (not full time): https://losangeles.craigslist.org/search/sof?employment_type=2&employment_type=3&employment_type=4
6. detail of job: https://losangeles.craigslist.org/lgb/sof/d/long-beach-web-programmer-position-open/7455560731.html
7. save into db, flag as unread
8. show into UI, shorted by created date

Run Django:
1. python manage.py runserver

Post detail:
- continent
- country
- city
- title
- post date
- is_read
- description
- extra_data {}
