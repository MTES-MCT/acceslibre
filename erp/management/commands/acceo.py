from erp.models import Erp

DRY_RUN = True
ACCEO_FIELDS = ["accueil_equipements_malentendants", "accueil_equipements_malentendants_presence"]
queryset = (
    Erp.objects.filter(source=Erp.SOURCE_ACCEO)
    .select_related("accessibilite")
    .filter(accessibilite__completion_rate=9)
    .order_by("created_at")
)
print(f"Found {queryset.count()} ERPS from acceo")

to_delete = 0
to_delete_name = 0
to_delete_cat = 0

for erp in queryset:
    possible_duplicates = Erp.objects.find_possible_duplicate(erp)
    if not possible_duplicates:
        continue

    same_level_of_data = Erp.objects.all_has_same_access_data(erp, possible_duplicates)

    if all([erp.nom.lower() == e.nom.lower() for e in possible_duplicates]):
        print("Will delete because same name")
        print(erp, possible_duplicates)

        if same_level_of_data:
            to_delete += len(possible_duplicates)
            to_delete_name += len(possible_duplicates)
            if not DRY_RUN:
                possible_duplicates.delete()
        else:
            if possible_duplicates.count() == 1:
                to_delete += 1
                to_delete_name += 1
                to_keep = possible_duplicates[0]
                if not DRY_RUN:
                    to_keep.merge_with(erp, fields=ACCEO_FIELDS)
                    erp.delete()
            else:
                print("-- Need to improve merge strategy in this case")

    # TODO is all of them comes from the acceo import ?
    # TODO wait for answer from team
    # if all([erp.activite == e.activite for e in possible_duplicates]):
    #     print("Will delete because same activities")
    #     print(erp, possible_duplicates)
    #     to_delete += len(possible_duplicates)
    #     to_delete_cat += len(possible_duplicates)
