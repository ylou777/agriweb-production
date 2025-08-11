from agriweb_source import app

if __name__ == '__main__':
    with app.test_client() as c:
        url = (
            "/rapport_commune_complet?commune=gueret"
            "&filter_rpg=false&rpg_min_area=1&rpg_max_area=1000"
            "&filter_parkings=true&parking_min_area=1500"
            "&filter_friches=true&friches_min_area=1000"
            "&filter_zones=false&zones_min_area=2500&zones_type_filter="
            "&filter_toitures=true&toitures_min_surface=1500"
            "&filter_by_distance=true&max_distance_bt=150&max_distance_hta=5000"
            "&poste_type_filter=BT&export_format=html"
        )
        r = c.get(url, headers={"Accept": "text/html"})
        print('status:', r.status_code)
        print('content-type:', r.headers.get('Content-Type'))
        data = r.get_data()
        print('length:', len(data))
        print('head:', data[:200])
