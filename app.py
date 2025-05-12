import flask, sqlite3, os 
from flask import render_template, request, redirect, url_for

app = flask.Flask(__name__)

# Global Dictionary
info = {} 
info['logIN'] = False
info['currentUser'] = [] # 0 is ID, 1 is Name 
info['currentGroup'] = "" 

@app.route('/')
def home():
    if len(info['currentUser']) == 2:
        acct = info['currentUser'][1]
    else:
        acct = None 
    return render_template('home.html', status = info['logIN'], acc = acct, update = False, join = False, leave = False)
	
@app.route('/c', methods=['GET','POST'])
def create():
    daysD = {'M':"Monday",'T':'Tuesday','W':'Wednesday','Th':'Thursday','F':'Friday'}
    if info['logIN'] == True:
        if request.method == 'POST':
            gID = request.form['number']
            lID = request.form['leaderNo']
            name = request.form['gName']
            cat = request.form['cat']
            day = request.form.getlist('day') # In order to get the multiple data points from Checkbox input type 
            time = request.form['timings']
            summ = request.form['summary']

            days = ""
            for item in day:
                days += item
                days += ','
            
            db = sqlite3.connect('database.db')
            db.execute('INSERT INTO Groups(GroupID,Name,LeaderID,Day,Time,Category,Summary) VALUES(?,?,?,?,?,?,?)', (str(gID),name,str(lID),days[:-1],str(time),cat,summ))
            db.commit()

            db.close()
            return render_template('home.html',status = info['logIN'], acc=info['currentUser'][1], update = False, join = False, leave = False)
        else:
            # Opening database to get most recent ID 
            db = sqlite3.connect('database.db')
            cursor = db.execute('Select GroupID from Groups Order By GroupID Desc limit 1')
            # Above code gets the most recent ID by sorting in descending order
            oldID = cursor.fetchone()
            newID = int(oldID[0]) + 1

            #return str(newID)
            return render_template('create.html', gID = newID, lID = info['currentUser'][0])
    else:
        return redirect('/LogIn')

@app.route('/LogIn', methods=['GET','POST'])
def LogIn():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pw']

        # Opening DB to find the password of the email
        db = sqlite3.connect('database.db')
        cursor = db.execute('Select Password,ID,Name FROM Students WHERE Email like ?', (email,))
        pw = cursor.fetchone()

        if pw[0] == password:
            info['logIN'] = True 
            info['currentUser'] = [pw[1],pw[2]]
            # return str(logIn)
            # return str(currID)
            return render_template('home.html', status = info['logIN'], acc = info['currentUser'][1], update = False, join = False, leave = False)
            # return redirect(url_for('home', status=True, acc = pw[2], logIn=True))
        
        else:
            return render_template('login.html', error = True)  
    else:
        return render_template('login.html', error = False) 

@app.route('/Signin', methods=['GET','POST'])
def SignIn():
    if request.method == 'POST':
        currID = request.form['ID']
        name = request.form['name']
        phone = request.form['number']
        email = request.form['email']
        pw = request.form['pw']
        su = [] # Since when a group is created, there's no sign ups (leader excluded since they will always be a part of the group

        db = sqlite3.connect('database.db')

        # 1) Check for repeat emails (alternatively could find the length of emails like the email submitted)
        match = False
        cursor = db.execute('Select Email from Students')
        lst = cursor.fetchall()
        for item in lst:
            if item[0] == email:
                match = True

        if match == True:
            return render_template('signin.html', error = True)

        # 2) Add the new information
        else: 
            db.execute('INSERT INTO Students(ID,Name,Email,Password,Phone) VALUES(?,?,?,?,?)', (currID,name,email,pw,phone))
            db.commit() # Can't forget to save changes 
        db.close()
        
        info['logIN'] = True 
        info['currentUser'] = [currID, name]
        return render_template('home.html', status = info['logIN'], acc = info['currentUser'][1], update = False, join = False, leave = False) 
        
    else: 
        # Connecting to Db to extract latest Student ID
        db = sqlite3.connect('database.db')
        cursor = db.execute('Select ID from Students Order By ID Desc Limit 1')
        oldID = cursor.fetchone()
        newID = int(oldID[0]) + 1
        db.close() 
        
        return render_template('signin.html', sID = newID, error = False)

@app.route('/Find')
def Find():

    groups = [] # For displaying purposes
    db = sqlite3.connect('database.db')
    cursor = db.execute('Select GroupID, Name, Summary From Groups')
    for item in cursor.fetchall():
        groups.append(item)
    return render_template('find.html', groups=groups, acc = info['currentUser'])

@app.route('/Filter', methods=['GET','POST'])
def Filter():
    if request.method == 'POST':
        cat = request.form['category']
        day = request.form['day']
        time = request.form.getlist('timings') # Returns a List 
        # Day is not using checkbox as there's only 5 days
        # VS Timings which has at least 12, only looking at one at a time is bad user design

        valid = [] # A list for the groups

        db = sqlite3.connect('database.db')
        # Going through all the filters one by one
        # 1) Day
        dFilt = '%' + day + '%'
        cursor = db.execute('SELECT GroupID, Name, Summary From Groups Where Day like ?', (dFilt,)) 
        for grp in cursor.fetchall():
            if grp not in valid:
                valid.append(grp)

        # 2) Category
        cursor = db.execute('SELECT GroupID, Name, Summary From Groups Where Category like ?', (cat,)) 
        for grp in cursor.fetchall():
            if grp not in valid:
                valid.append(grp)

        # 3) Timings
        cursor = db.execute('SELECT GroupID, Name, Summary, Time From Groups')
        grps = cursor.fetchall()
        for grp in grps:
            if grp[3] in day and grp not in valid: # grp[3] is the Time cuz of 0-indexing
                valid.append(grp)

        db.close()
        # return valid 
        return render_template('find.html', groups = valid) 
    else:
        
        # Defining lists inside the function so it's not global
        # These lists are to make sure options without a group aren't chosen
        days = []
        times = []
        cats = []

        db = sqlite3.connect('database.db')

        # Categories
        cursor = db.execute('Select Category from GROUPS Group By Category')
        lst = cursor.fetchall()
        for item in lst:
            print(item[0])
            cats.append(item[0])

        # Timings 
        cursor = db.execute('Select Time from GROUPS Group By Time Order By Time')
        # So at least the timings are in chronological order 
        lst = cursor.fetchall()
        for item in lst:
            print(item[0]) 
            times.append(item[0])

        # Days
        # I realised that it's almost guaranteed all five days will be there so why bother
        days = ['M','T','W','Th','F']
                

        db.close()
        return render_template('/filter.html',Time = times, Categories = cats, Days = days)
    
@app.route('/Group/<name>')
def showInfo(name):
    info['currentGrp'] = name
    daysD = {'M':"Monday",'T':'Tuesday','W':'Wednesday','Th':'Thursday','F':'Friday'}
    # ^^ Dictionary for days
    days = ''

    # Open Db to get all the Data
    db = sqlite3.connect('database.db')
    filt = "%" + name + "%" # To deal with annoying group names, presume someone is not going to create a group with a near exact replica of another's name
    cursor = db.execute('Select * from Groups where Name like ?', (filt,))
    lst = cursor.fetchone()
    
    gName = lst[1]
    time = lst[4]
    cat = lst[5]
    summary = lst[6] 

    # Days 
    day = lst[3].split(',')
    for item in day:
        days += daysD[item]
        days += ', '

    # Leader Name
    lID = lst[2]
    cursor = db.execute('Select Name,Email from Students where ID like ?', (lID,))
    sID = cursor.fetchone() 
    db.close()

    if len(info['currentUser']) == 2: # to ensure its a logged in User
        current = info['currentUser'][1]
    else:
        current = "None" 
    
    return render_template('group.html', name=name, days=days[:-2], timing = time, summary = summary, leader = sID[0], email = sID[1], curr=current, signUp = lst[7])

@app.route('/Update', methods=['GET','POST'])
def update():

    # As this page can only be accessed by the leader of the corresponding group
    # AKA must be logged in, no need to check for Log In

    if request.method == 'POST':
        name = request.form['gName']
        cat = request.form['cat']
        day = request.form.getlist('day') # In order to get the multiple data points from Checkbox input type 
        time = request.form['timings']
        summ = request.form['summary']


        # Just need to edit the "Day" part to fit in with the format.
        days = ""
        for item in day:
            days += item
            days += ','

        db = sqlite3.connect('database.db')
        db.execute("Update Groups Set Name = ?, Day = ?, Time = ?, Category = ?, Summary = ? Where Name = ?", (name,days[:-1],time,cat,summ,info['currentGrp']))
        db.commit()
        db.close()

        #return redirect('/')
        return render_template('home.html', status = info['logIN'], acc=info['currentUser'][1], update = True, join = False, leave = False)

    else: # As this comes from the group page, can use the name as input
        db = sqlite3.connect('database.db')
        cursor = db.execute("Select * From Groups where Name like ?", (info['currentGrp'],)) 
        lst = cursor.fetchone()
        cat = lst[5]

        # Reformatting the days String into a list
        days = lst[3].split(',')

        return render_template('update.html',name = lst[1], days=lst[3].split(','),dayLst = ['M','T','W','Th','F'], cate = cat,timing = lst[4], summ = lst[6])
        #return grp

@app.route('/LogOut')
def logOut():

    if info['logIN'] == True: 
        info['logIN'] = False
        info['currentUser'] = []
    return redirect('/')

@app.route('/Join')
def join():

    if info['logIN'] == True: # Making sure User is logged in
        # Open DB to get list of Sign Ups
        db = sqlite3.connect('database.db')
        cursor = db.execute("Select SignUps from Groups where Name = ?", (info['currentGrp'],))
        lst = cursor.fetchone()[0]

        if info['currentUser'][1] not in lst:
            lst += (info['currentUser'][1])
            lst += ','
            
            db.execute("Update Groups Set SignUps = ? Where Name = ?", (lst,info['currentGrp']))
            db.commit()
            joined = True 

        else:
            joined = 'Error'

        db.close()
        #return str(joined)
        return render_template('home.html', status = info['logIN'], acc=info['currentUser'][1], update = False, join = joined, leave = False)

    else:
        return redirect('/LogIn')

@app.route('/account')
def showAcc():

    # as the link to this doesn't appear unless the user is logged in,
    # There's no need to perform a check
    db = sqlite3.connect('database.db')

    # Get student info
    cursor = db.execute('Select Name,Email,Phone from Students where ID=?', (info['currentUser'][0],))
    user = cursor.fetchone()
    
    name = user[0]
    email = user[1]
    phone = user[2]

    cursor = db.execute('Select Name, SignUps from Groups where LeaderID = ?', (info['currentUser'][0],))
    grps = cursor.fetchall()
    if grps == None: # User is the leader of 0 groups, set the str to smth of len 0
        groups = "None"
    else: 
        groups = grps

    # Sign Ups
    filt = '%' + info['currentUser'][1] + '%'
    cursor = db.execute('Select g.Name,s.Name from Groups as g INNER JOIN Students as s ON s.ID = g.LeaderID where SignUps like ?', (filt,))
    signUps = cursor.fetchall()

    # Data is in the format ((group name, group leader),...) 
    if signUps == None:
        su = "None"
    else:
        su = signUps
        
    db.close()
            

    return render_template('account.html',name=name,email=email,phone=phone,groups=groups,signUps=su)

@app.route('/leave')
def leave():

    db = sqlite3.connect('database.db')
    # Coming from group page so the current group ID would be the group that you want to leave
    cursor = db.execute('Select SignUps from Groups Where Name = ?', (info['currentGrp'],))
    sList = cursor.fetchone()
    if info['currentUser'][1] in sList[0]:
        leave = True
        sign = sList[0].split(',')
        lst = '' # To hold the signups list to reinsert back into database
        for item in sign:
            if item != info['currentUser'][1]:
                lst += item
                lst += ','

        db.execute('Update Groups Set SignUps = ? Where Name = ?', (lst[:-2],info['currentGrp'],))
        db.commit() 
        
    else:
        leave = "Error" # User is not in the group, just going to test for that situation

    db.close()
    #return sList
    return render_template('home.html', status = info['logIN'], acc = info['currentUser'][1], update = False, join = False, leave = leave) 
if __name__ == '__main__':
    app.run(debug=True)
