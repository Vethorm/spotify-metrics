# spotify-metrics

**Discontinued**: [Spotify cut significant API access to third party apps](https://www.androidpolice.com/spotify-new-api-terms-third-party-apps/)

---

This is a personal project that lets me scrape and visualize my recently played songs on Spotify along with some metrics about the listen history.

Some of the technologies used

- Python
  - [Dash](https://plotly.com/dash/)
    - Data App and Dashboard tool
    - Built on Plotly, React, and Flask
  - [Tekore](https://github.com/felix-hilden/tekore)
    - Spotify API client
- MongoDB
- Docker

## Limitations of the project

- Project is currently limited to only my listen history
- Spotify only allows you to request the 50 most recent songs
  - if you listen to 51 songs you will not be able to get the 51 songs
  - Current solution: scrape the recently played endpoint on a sane interval
- Limited scope of data ingestion

## Deploying

### Deploying on my homelab

Deploying is luckily quite simple. First configure your `.env` and simply run `make`.

The application should then be defined at http://spotifymetrics.your.domain assuming you have enabled traefik. If traefik is disabled then the site should still be accessible from http://localhost:9990

To view the mongo database we can use express at http://localhost:8481

### Deploying without homelab

Configure your `.env` and simply run `make`.

### Getting the access and refresh tokens

- Install spotify-scraper to a python environment
- Run `get-new-spotify-token`
  - Ensure you've correctly setup your spotify API application with spotify otherwise this won't work

## Roadmap

- [x] Working application
- [ ] Allow for other users to see their listen history
- [ ] Separate front and backend
  - [ ] Build a Python backend with FastAPI
  - [ ] Build a client side rendered frontend with a JavaScript framework
- [ ] Implement new visualizations !

## Resources

### Flask

- [Flask applicative dive](https://hackersandslackers.com/your-first-flask-application/)

### Frontend

- [Stylizing your dash](https://realpython.com/python-dash/)
- [Admin template](https://github.com/themeselection/sneat-html-admin-template-free)
  - [Demo](https://github.com/themeselection/sneat-html-admin-template-free)


