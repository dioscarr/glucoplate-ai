# GlucoPlate AI

AI-powered diabetes-friendly recipe and meal-planning system designed as a portfolio-grade AI system architecture project.

> **Important:** This project is for education, meal planning support, and software architecture demonstration only. It does not diagnose diabetes, treat medical conditions, adjust medication, or replace guidance from a clinician or registered dietitian.

## Vision

GlucoPlate AI helps users discover diabetes-conscious meals, generate culturally relevant recipes, plan weekly meals, create grocery lists, and understand nutrition tradeoffs using AI-assisted workflows with safety guardrails.

## Why This Project Exists

Many recipe apps generate meals without considering health constraints, cultural food preferences, portioning, or safety boundaries. GlucoPlate AI is designed to show how an AI product can combine:

- user-centered product design
- health-aware guardrails
- recipe generation
- nutrition validation
- culturally relevant food recommendations
- clean Python architecture
- API-first engineering

## Core Capabilities

- Diabetes-friendly recipe generation
- Meal planning
- Grocery list generation
- Ingredient substitutions
- Nutrition estimation
- Safety guardrail review
- Cultural recipe support
- User preference personalization

## High-Level Architecture

```text
User Profile
   ↓
Preferences + Health Constraints
   ↓
Recipe Knowledge Base
   ↓
AI Recipe Generator
   ↓
Nutrition Validator
   ↓
Safety Guardrails
   ↓
Recipe / Meal Plan / Grocery List
```

## Python Stack

Initial target stack:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local development
- PostgreSQL for production
- pytest

## Repository Structure

```text
app/
  api/
  core/
  models/
  schemas/
  services/
  safety/
docs/
  product/
  architecture/
  ai-safety/
  data-model/
tests/
```

## Safety Principles

The system must:

- Avoid medical diagnosis.
- Avoid medication or insulin adjustment advice.
- Avoid claims that recipes cure diabetes.
- Flag unsafe recommendations.
- Explain nutrition tradeoffs clearly.
- Encourage professional medical guidance for personal care decisions.

## Current Status

Architecture and MVP foundation.