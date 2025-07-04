from geopy.distance import geodesic

def interpolate_points(coords, distance_m):
    if not coords:
        return []

    new_points = [coords[0]]

    for i in range(1, len(coords)):
        start = coords[i - 1]
        end = coords[i]
        segment_dist = geodesic((start[1], start[0]), (end[1], end[0])).meters

        if segment_dist <= distance_m:
            new_points.append(end)
            continue

        num_points = int(segment_dist // distance_m)

        for n in range(1, num_points + 1):
            fraction = n * distance_m / segment_dist
            lon = start[0] + (end[0] - start[0]) * fraction
            lat = start[1] + (end[1] - start[1]) * fraction
            new_points.append((lon, lat))

        if new_points[-1] != end:
            new_points.append(end)

    return new_points
