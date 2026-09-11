"""
DIAL FOR SERVICE - Advanced Booking Features
Helpers for nearby-worker ranking, booking tracker stages, ETA, notifications
and dashboard analytics. These helpers are intentionally framework-light.
"""
from math import radians, sin, cos, asin, sqrt

TRACKER_STAGES = [
    ("pending", "Booking Requested", "Request submitted"),
    ("accepted", "Worker Accepted", "Worker accepted the request"),
    ("on_the_way", "Worker On The Way", "Worker is travelling to the customer"),
    ("arrived", "Worker Arrived", "Worker reached the customer"),
    ("in_progress", "Work In Progress", "Service work has started"),
    ("completed", "Completed", "Service completed"),
    ("cancelled", "Cancelled", "Booking cancelled"),
]

def haversine_km(lat1, lon1, lat2, lon2):
    """Return straight-line distance in kilometres."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    p = 0.017453292519943295
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p)*(1-cos((lon2-lon1)*p))/2
    return 12742 * asin(sqrt(max(0, a)))

def rank_workers_by_distance(workers, customer_lat, customer_lon):
    """Return workers sorted by GPS distance; unavailable coordinates go last."""
    ranked=[]
    for w in workers:
        lat=getattr(w,"latitude",None)
        lon=getattr(w,"longitude",None)
        d=haversine_km(customer_lat,customer_lon,lat,lon)
        ranked.append((d if d is not None else float("inf"), w))
    return [w for _,w in sorted(ranked,key=lambda x:x[0])]

def tracker_stage(status):
    for key,label,description in TRACKER_STAGES:
        if status == key:
            return {"key":key,"label":label,"description":description}
    return {"key":status,"label":str(status).replace("_"," ").title(),"description":""}

def tracker_progress(status, progress_percent=None):
    if progress_percent is not None:
        return max(0,min(100,int(progress_percent)))
    defaults={"pending":0,"accepted":10,"on_the_way":35,"arrived":50,"in_progress":70,"completed":100,"cancelled":0}
    return defaults.get(status,0)

def eta_text(minutes):
    if minutes is None: return "ETA not available"
    minutes=max(0,int(minutes))
    if minutes < 1: return "Arriving now"
    if minutes < 60: return f"{minutes} min"
    h,m=divmod(minutes,60)
    return f"{h} hr {m} min" if m else f"{h} hr"

def booking_notification(status):
    messages={
        "pending":"Your service request has been sent.",
        "accepted":"Your worker accepted the booking.",
        "on_the_way":"Your worker is on the way.",
        "arrived":"Your worker has arrived.",
        "in_progress":"Work has started.",
        "completed":"Your service has been completed.",
        "cancelled":"Your booking was cancelled.",
    }
    return messages.get(status,"Booking status updated.")

def dashboard_stats(bookings):
    stats={"total":0,"pending":0,"accepted":0,"on_the_way":0,"arrived":0,"in_progress":0,"completed":0,"cancelled":0}
    for b in bookings:
        s=getattr(b,"status","")
        stats["total"]+=1
        if s in stats: stats[s]+=1
    return stats
