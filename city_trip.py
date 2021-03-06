import helpers
import psycopg2
import os
import ast
import json
import numpy as np
from sklearn.cluster import KMeans

current_path= os.getcwd()
with open(current_path + '/api_key_list.config') as key_file:
    api_key_list = json.load(key_file)
api_key = api_key_list["distance_api_key_list"]
conn_str = api_key_list["conn_str"]

def get_fulltrip_data(state, city, n_days, full_day=True, regular=True, debug=True, visible=True):
    '''
    Get the default full trip data for each city(county)
    '''
    counties = helpers.find_county(state, city)
    n_days = int(n_days)
    if counties:
        counties_str = '-'.join(counties).upper().replace(' ','-')
        full_trip_id = '-'.join([str(state.upper()), counties_str,str(int(regular)), str(n_days)])
    else:
        full_trip_id = '-'.join([str(state.upper()), str(city.upper().replace(' ','-')),str(int(regular)), str(n_days)])
    if not helpers.check_full_trip_id(full_trip_id):
        trip_location_ids, full_trip_details,county_list_info =[],[],[]
        county_list_info = helpers.db_start_location(counties, state, city)
        county_list_info = np.array(county_list_info)
        if county_list_info.shape[0] == 0:
            print city, state, county, "is not in our database!!!!?"
            return city, state, county
        new_end_day = max(county_list_info.shape[0]/6, 1)
        if  n_days > new_end_day:
            return get_fulltrip_data(state, city, new_end_day) 
        poi_coords = county_list_info[:,1:3]
        kmeans = KMeans(n_clusters=n_days).fit(poi_coords)
        day_labels = kmeans.labels_
        day_order = helpers.kmeans_leabels_day_order(day_labels)
        not_visited_poi_lst = []
        for i,v in enumerate(day_order):
            if counties:
                counties_str = '-'.join(counties).upper().replace(' ','-')
                day_trip_id = '-'.join([str(state.upper()), counties_str,str(int(regular)), str(n_days), str(i)])
            else:
                day_trip_id = '-'.join([str(state).upper(), str(city.upper().replace(' ','-')),str(int(regular)), str(n_days),str(i)])
            current_events, big_ix, small_ix, med_ix = [],[],[],[]
            for ix, label in enumerate(day_labels):
                if label == v:
                    time = county_list_info[ix,3]
                    event_ix = county_list_info[ix,0]
                    current_events.append(event_ix)
                    if time > 180 :
                        big_ix.append(ix)
                    elif time >= 120 :
                        med_ix.append(ix)
                    else:
                        small_ix.append(ix)
            big_ = helpers.sorted_events(county_list_info, big_ix)
            med_ = helpers.sorted_events(county_list_info, med_ix)
            small_ = helpers.sorted_events(county_list_info, small_ix)
            event_ids, event_type = helpers.create_event_id_list(big_, med_, small_)
            event_ids, event_type = helpers.db_event_cloest_distance(event_ids = event_ids, event_type = event_type, city_name = city)
            event_ids, driving_time_list, walking_time_list = helpers.db_google_driving_walking_time(event_ids, event_type)
            event_ids, driving_time_list, walking_time_list, total_time_spent, not_visited_poi_lst = \
                helpers.db_adjust_events(event_ids, driving_time_list, walking_time_list, not_visited_poi_lst, event_type, city)
            details = helpers.db_day_trip_details(event_ids, i)
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute('select max(index) from day_trip_table;')
            max_index = cur.fetchone()[0]
            index = max_index + 1
            if helpers.check_day_trip_id(day_trip_id):
                cur.execute("SELECT index FROM day_trip_table WHERE trip_locations_id = '%s';" % (day_trip_id))
                cur = conn.cursor()                     
                index = cur.fetchone()[0]
                cur.execute("DELETE FROM day_trip_table WHERE trip_locations_id = '%s';" % (day_trip_id))
                conn.commit()
            if counties:
                cur.execute("insert into day_trip_table (index, trip_locations_id, full_day, regular, county, state, details, event_type, event_ids) VALUES ( %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s');" %(index, day_trip_id, full_day, regular, json.dumps(counties), state, str(details).replace("'", "''"), event_type, str(list(event_ids))))
            else:
                cur.execute("insert into day_trip_table (index, trip_locations_id, full_day, regular, county, state, details, event_type, event_ids) VALUES ( %s, '%s', %s, %s, '%s', '%s', '%s', '%s', '%s');" %(index, day_trip_id, full_day, regular, counties, state, str(details).replace("'", "''"), event_type, str(list(event_ids))))
            conn.commit()
            conn.close()
            trip_location_ids.append(day_trip_id)
            full_trip_details.extend(details)
        username_id = 1
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("select max(index) from full_trip_table;")
        full_trip_index = cur.fetchone()[0] + 1
        if counties:
            cur.execute("insert into full_trip_table(index, username_id, full_trip_id,trip_location_ids, regular, county, state, details, n_days, visible) VALUES (%s, %s, '%s', '%s', %s, '%s', '%s', '%s', %s, %s);" %(full_trip_index, username_id  , full_trip_id, str(trip_location_ids).replace("'","''"), regular, json.dumps(counties), state, str(full_trip_details).replace("'", "''"), n_days, visible))
        else:
            cur.execute("insert into full_trip_table(index, username_id, full_trip_id,trip_location_ids, regular, county, state, details, n_days, visible) VALUES (%s, %s, '%s', '%s', %s, '%s', '%s', '%s', %s, %s);" %(full_trip_index, username_id  , full_trip_id, str(trip_location_ids).replace("'","''"), regular, counties, state, str(full_trip_details).replace("'", "''"), n_days, visible))
        conn.commit()
        conn.close()
        print "finish update %s, %s into database" %(state, str(counties))
    else:
        print "%s, %s already in database" %(state, str(counties))
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("select trip_location_ids, details from full_trip_table where full_trip_id = '%s';" % (full_trip_id))
        trip_location_ids, details = cur.fetchone()
        conn.close()
        full_trip_details = ast.literal_eval(details)
        trip_location_ids = ast.literal_eval(trip_location_ids)
    return full_trip_id, full_trip_details, trip_location_ids

def create_day_trip(day_labels, city_poi_list_info, city, state, regular, available_days, i, v, not_visited_poi_lst):
    day_trip_id = '-'.join([str(state).upper().replace(' ','-'), str(city.upper().replace(' ','-')),str(int(regular)), str(available_days),str(i)])
    big_ix, med_ix,small_ix = helpers.create_big_med_small_lst(day_labels, city_poi_list_info, v)
    event_ids, event_type = helpers.create_event_id_list(big_ix, med_ix, small_ix)
    event_ids, event_type = helpers.db_event_cloest_distance(event_ids = event_ids, event_type = event_type, city_name = city)
    event_ids, driving_time_list, walking_time_list = helpers.db_google_driving_walking_time(event_ids, event_type)
    event_ids, driving_time_list, walking_time_list, total_time_spent, not_visited_poi_lst = \
        helpers.db_adjust_events(event_ids, driving_time_list, walking_time_list, not_visited_poi_lst, event_type, city)
    details = helpers.db_city_day_trip_details(event_ids, i, city, state)
    event_ids = event_ids.tolist()
    return day_trip_id, event_ids, event_type, details, not_visited_poi_lst

def get_city_trip_data(state, city, n_days, full_day=True, regular=True, visit_speed='normal', visible=True):
    '''
    Get the default full trip data for each city(county)
    '''
    n_days = int(n_days)
    if visit_speed == 'normal':
        num_poi_per_day = 8
    else:
        num_poi_per_day = 8
    full_trip_id = '-'.join([str(state.upper()).replace(' ','-'), str(city.upper().replace(' ','-')),str(int(regular)), str(n_days)])
    if not helpers.check_full_trip_id_city(full_trip_id):
        trip_location_ids, full_trip_details =[],[]
        city_poi_list_info = helpers.db_start_city_poi(city,state)
        available_days = len(city_poi_list_info)/num_poi_per_day
        available_surr_days, city_surr_poi_list_info = 0, []
        city_day_labels, city_day_order, city_surr_day_labels,city_surr_day_order = [],[],[],[]
        if available_days < n_days:
            city_surr_poi_list_info, available_surr_days = helpers.db_city_and_surrounding_poi(city, state, n_days-available_days, num_poi_per_day)
        else: 
            available_days = n_days
        if (not city_poi_list_info) and (not city_surr_poi_list_info):
            print 'there is no availables pois for the city {0}, {1} and surrounding areas'.format(city, state)
            available_days = 0
            return full_trip_id, [], [], available_days
        if available_days > 0:
            city_poi_coords_lst = np.array(city_poi_list_info)[:,1:3]
            kmeans = KMeans(n_clusters=available_days).fit(city_poi_coords_lst)
            city_day_labels = kmeans.labels_
            city_day_order = helpers.kmeans_leabels_day_order(city_day_labels)
        if available_surr_days > 0:
            city_surr_poi_coords_lst = np.array(city_surr_poi_list_info)[:,1:3]
            kmeans = KMeans(n_clusters=available_surr_days).fit(city_surr_poi_coords_lst)
            city_surr_day_labels = kmeans.labels_
            city_surr_day_order = helpers.kmeans_leabels_day_order(city_surr_day_labels)
            poi_list_info = city_poi_list_info + city_surr_poi_list_info 
            day_labels = np.concatenate((city_day_labels, [surr_label+available_days for surr_label in city_surr_day_labels]), axis=0)
            day_order = np.concatenate((city_day_order, [order+available_days for order in city_surr_day_order]), axis=0)
            total_available_days = available_days+available_surr_days
        else:
            poi_list_info = city_poi_list_info
            day_labels = city_day_labels 
            day_order = city_day_order 
            total_available_days = available_days
        not_visited_poi_lst = []

        old_big_ix, old_med_ix,old_small_ix = [],[],[]

        for i,v in enumerate(day_order):
            day_trip_id = '-'.join([str(state).upper().replace(' ','-'), str(city.upper().replace(' ','-')),str(int(regular)), str(total_available_days),str(i)])
            big_ix, med_ix, small_ix = helpers.create_big_med_small_lst(day_labels, poi_list_info, v)
            city_poi_list_info =  np.array(poi_list_info)[:,:7].astype(np.float)
            big_ix, med_ix, small_ix = helpers.sorted_events(city_poi_list_info, big_ix, old_big_ix),helpers.sorted_events(city_poi_list_info, med_ix, old_med_ix),helpers.sorted_events(city_poi_list_info, small_ix,old_small_ix)
            event_ids, event_type = helpers.create_event_id_list(big_ix, med_ix, small_ix)
            event_ids, event_type = helpers.db_event_cloest_distance(event_ids = event_ids, event_type = event_type, city_name = city)
            
            event_ids, driving_time_list, walking_time_list = helpers.db_google_driving_walking_time(event_ids, event_type)
            event_ids, driving_time_list, walking_time_list, total_time_spent, not_visited_poi_lst = \
                helpers.db_adjust_events(event_ids, driving_time_list, walking_time_list, not_visited_poi_lst, event_type, city)
            old_big_ix = np.array([b for b in big_ix if b[0] not in event_ids])
            old_med_ix =np.array([m for m in med_ix if m[0] not in event_ids])
            old_small_ix = np.array([s for s in small_ix if s[0] not in event_ids])
            
            details = helpers.db_city_day_trip_details(event_ids, i, city, state)

            event_ids = map(int,event_ids)
            conn = psycopg2.connect(conn_str)
            cur = conn.cursor()
            cur.execute('SELECT max(index) FROM day_trip_table_city;')
            max_index = cur.fetchone()[0]
            index = max_index + 1
            if helpers.check_day_trip_id_city(day_trip_id):
                conn = psycopg2.connect(conn_str)
                cur = conn.cursor()  
                cur.execute("SELECT index FROM day_trip_table_city WHERE trip_locations_id = %s;",(day_trip_id,))
                index = cur.fetchone()[0]
                cur.execute("DELETE FROM day_trip_table_city WHERE trip_locations_id = %s;",(day_trip_id,))
                conn.commit()
            cur.execute("INSERT INTO day_trip_table_city (index, trip_locations_id, full_day, regular, city, state, details, event_type, event_ids) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s);",(index, day_trip_id, full_day, regular, city, state, json.dumps(details), event_type, json.dumps(event_ids)))
            conn.commit()
            conn.close()
            trip_location_ids.append(day_trip_id)
            full_trip_details.extend(details)
        username_id = 1
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("SELECT max(index) FROM full_trip_table_city;")
        full_trip_index = cur.fetchone()[0] + 1

        cur.execute("INSERT INTO full_trip_table_city (index, username_id, full_trip_id, trip_location_ids, regular, city, state, details, n_days, visible) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);" ,(full_trip_index, username_id  , full_trip_id, json.dumps(trip_location_ids), regular, city, state, json.dumps(full_trip_details), n_days, visible))

        conn.commit()
        conn.close()
        print "finish update %s, %s into database" %(state, city)
    else:
        print "%s, %s already in database" %(state, city)
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        cur.execute("select trip_location_ids, details from full_trip_table_city where full_trip_id = '%s';" % (full_trip_id))
        trip_location_ids, details = cur.fetchone()
        conn.close()
        full_trip_details = json.loads(details)
        trip_location_ids = json.loads(trip_location_ids)
        trip_location_ids =[str(x) for x in trip_location_ids]
        print trip_location_ids, type(trip_location_ids)
    return full_trip_id, full_trip_details, trip_location_ids
   

if __name__ == '__main__':
    import time
    start_t = time.time()
    origin_city = 'San Jose'
    origin_state = 'California'
    print origin_city, origin_state
    days = [1,2,3,4,5]
    for n_days in days:
        full_trip_id, full_trip_details, trip_location_ids = get_city_trip_data(origin_state, origin_city, n_days)
        # full_trip_id, full_trip_details, trip_location_ids = get_fulltrip_data(origin_state, origin_city, n_days)
        # print type(full_trip_details), type(trip_location_ids)
        # for i in trip_location_ids:
        #     print type(i)

    print time.time()-start_t

