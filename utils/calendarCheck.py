import urllib.request
#import threading
#import time
#from apscheduler.schedulers.background import BackgroundScheduler

#print( "you shall pass" )

allowedRooms = []

icalendarURL = 'https://mytimetable.tudelft.nl/ical?5d5d3020&group=false&eu=ZWprb29pag==&h=A_j7yzgOJs8e2YmL9Rq6uVpLjN2FLaLDaNvPd1fIWdg='

#try:
#   with urllib.request.urlopen( icalendarURL ) as f:
#      print(f.read().decode('utf-8'))
#except urllib.error.URLError as e:
#   print(e.reason)

#sched = BackgroundScheduler()

#ics_file = "D:/Users/Eric/Downloads/timetable_2023-10-25 (1).ics"

print( "path to ics file: " +  icalendarURL + "\n\n" )

#def findRooms():
currTime = datetime.datetime.now( timezone('UTC') )
print( "Now it is: " ) 
print( currTime )
print( "\n\n" )
#allowedRooms = []
    
with urllib.request.urlopen( icalendarURL ) as f:
    calendar = icalendar.Calendar.from_ical(f.read())
            
        
    for event in calendar.walk('VEVENT'):
        start_time = event['DTSTART'].dt.astimezone( timezone('UTC') )
        end_time = event['DTEND'].dt.astimezone( timezone('UTC') )
        #start_time_utc = start_time.dt.astimezone(timezone('UTC'))
        #print( event.get( "SUMMARY" ) )
        #print( end_time )
        #print( start_time )
        #print( end_time )
        #print( event.get("SUMMARY") + " " + event.get("LOCATION") + " " + event.get( "STATUS" ) )
        #print( "\n\n" )
            
        timeToEvent = start_time - currTime
        #print( "time to event: " )
        #print( timeToEvent )
        #print( "\n\n" )
            
        timeToEnd = end_time - currTime
            
        if ( ( ( ( timeToEnd.total_seconds() ) / 60 ) > 0 ) and ( ( ( timeToEvent.total_seconds() ) / 60 ) < 30 ) and event.get( "STATUS" ) == "CONFIRMED" ): #and timeToEvent.minutes < 30:
            allowedRooms.append( event )
            #print( "course of interest at location: " )
            #print( event.get("LOCATION") )
            #print( "\n\n" )
                
print( "locations of interest: \n\n" )
    
for room in allowedRooms:
    print( room.get("LOCATION") + "\n" )
    
    #threading.Timer(60, findRooms).start()
        
#threading.Timer(60, findRooms).start()
# seconds can be replaced with minutes, hours, or days
#sched.add_job( findRooms, 'interval', minutes=1 )
#sched.start()

#while 1:
#    if input( 'press q to exit' ) == 'q':
#        break
    
#sched.shutdown()
