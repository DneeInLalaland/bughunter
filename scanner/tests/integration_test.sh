#!/bin/bash

echo "=================================="
echo "Integration Test Script"
echo "=================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -e "\n${YELLOW}Testing: $name${NC}"
    response=$(curl -s $url)
    
    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ $name: PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ $name: FAIL${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Check if Docker is running
echo -e "\n${YELLOW}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running!${NC}"
    echo "Please start Docker Desktop first."
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if services are running
echo -e "\n${YELLOW}Checking if services are running...${NC}"

# Test Scanner API
test_endpoint "Scanner API" "http://localhost:5001/health" "healthy"
scanner_status=$?

# Test ML API (ถ้ามี)
if docker-compose ps | grep -q "ml_api"; then
    test_endpoint "ML API" "http://localhost:5000/health" "healthy"
    ml_status=$?
else
    echo -e "${YELLOW}⊘ ML API: NOT DEPLOYED YET${NC}"
    ml_status=0
fi

# Test Backend API (ถ้ามี)
if docker-compose ps | grep -q "backend_api"; then
    test_endpoint "Backend API" "http://localhost:8000/health" "healthy"
    backend_status=$?
else
    echo -e "${YELLOW}⊘ Backend API: NOT DEPLOYED YET${NC}"
    backend_status=0
fi

# Check Frontend (ถ้ามี)
if docker-compose ps | grep -q "frontend_app"; then
    echo -e "\n${YELLOW}Testing: Frontend${NC}"
    if curl -s http://localhost > /dev/null; then
        echo -e "${GREEN}✓ Frontend: PASS${NC}"
        frontend_status=0
    else
        echo -e "${RED}✗ Frontend: FAIL${NC}"
        frontend_status=1
    fi
else
    echo -e "${YELLOW}⊘ Frontend: NOT DEPLOYED YET${NC}"
    frontend_status=0
fi

# Check PostgreSQL
echo -e "\n${YELLOW}Testing: PostgreSQL${NC}"
if docker-compose exec -T postgres pg_isready -U scanuser > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL: PASS${NC}"
    db_status=0
else
    echo -e "${RED}✗ PostgreSQL: FAIL${NC}"
    db_status=1
fi

# Summary
echo -e "\n=================================="
echo "Test Summary"
echo "=================================="

total=5
passed=$((5 - scanner_status - ml_status - backend_status - frontend_status - db_status))

echo "Passed: $passed/$total"

if [ $scanner_status -eq 0 ] && [ $db_status -eq 0 ]; then
    echo -e "${GREEN}Core services (Scanner + Database) are running!${NC}"
    exit 0
else
    echo -e "${RED}Some core services are not running. Please check above.${NC}"
    exit 1
fi