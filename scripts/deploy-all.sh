#!/bin/bash
# Deploy all GYMPT services to EKS

set -e

ENV=${1:-prod}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  GYMPT Full Stack Deployment - ${ENV}${NC}"
echo -e "${GREEN}========================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Deploy services in order
echo -e "${YELLOW}Deploying Backend API...${NC}"
bash ${SCRIPT_DIR}/deploy-backend.sh ${ENV}

echo ""
echo -e "${YELLOW}Deploying Agent Service...${NC}"
bash ${SCRIPT_DIR}/deploy-agent.sh ${ENV}

echo ""
echo -e "${YELLOW}Deploying Frontend...${NC}"
bash ${SCRIPT_DIR}/deploy-frontend.sh ${ENV}

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Services Deployed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${ENV}"
echo -e "Frontend: https://g2mpt.com"
echo -e "Backend API: https://api.g2mpt.com"
echo -e "Argo CD: https://argocd.g2mpt.com"
echo -e ""
echo -e "Next steps:"
echo -e "  1. Verify all pods are running:"
echo -e "     kubectl get pods -n gympt-${ENV}"
echo -e "  2. Check service health:"
echo -e "     curl https://api.g2mpt.com/api/v1/health"
echo -e "  3. Monitor logs:"
echo -e "     kubectl logs -f deployment/backend-api -n gympt-${ENV}"
