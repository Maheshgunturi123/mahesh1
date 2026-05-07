# GymTrack Deployment Guide

## Railway Setup (to be completed in Story 1.6)

### Prerequisites
- Railway account
- PostgreSQL add-on

### Environment Variables
Set all variables from `.env.example` in Railway dashboard.

### Deploy
```
gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT
```
