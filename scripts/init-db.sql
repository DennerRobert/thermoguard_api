-- ThermoGuard IoT API - Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create additional indexes for performance (optional)
-- These are created by Django migrations, but can be added here for explicit control

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE thermoguard_db TO thermoguard;


