#!/bin/bash
# Script para aplicar el fix del trigger check_single_base_uom

echo "Aplicando fix del trigger check_single_base_uom..."

# Aplicar en local
docker-compose exec -T db psql -U ferreteria -d ferreteria < db/migrations/FIX_check_single_base_uom_trigger.sql

if [ $? -eq 0 ]; then
    echo "✓ Fix aplicado exitosamente en LOCAL"
else
    echo "✗ Error al aplicar fix en LOCAL"
    exit 1
fi

echo ""
echo "Para aplicar en PRODUCCIÓN, ejecutar:"psql -U usuario -d database < db/migrations/FIX_check_single_base_uom_trigger.sql
echo ""
