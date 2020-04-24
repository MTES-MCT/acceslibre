#!/usr/bin/env bash


mkdir -p graphs
./manage.py graph_models -g -I Accessibilite,Activite,Erp,EquipementMalentendant,Label -o graphs/All.png
./manage.py graph_models --hide-edge-labels -n -I Accessibilite -o graphs/Accessibilite.png
./manage.py graph_models --hide-edge-labels -n -I Activite -o graphs/Activite.png
./manage.py graph_models --hide-edge-labels -n -I Erp -o graphs/Erp.png
./manage.py graph_models --hide-edge-labels -n -I EquipementMalentendant -o graphs/EquipementMalentendant.png
./manage.py graph_models --hide-edge-labels -n -I Label -o graphs/Label.png
