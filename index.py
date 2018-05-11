import boto3, os, re, base64, json
from flask import Flask, render_template, request, redirect, url_for

#need this
app = Flask(__name__)
ddb = boto3.resource('dynamodb', region_name='us-east-1')
lmbd = boto3.client('lambda', region_name='us-east-1')
users = ddb.Table('users')
sessions = ddb.Table('sessions')

next_port = 5000
next_net = 1

@app.route('/', methods=['GET'])
def home():
        return render_template('home.html')

@app.route('/login', methods=['POST'])
def login():
        response = users.get_item(Key={
                'username': request.form['username']
        })
        if 'Item' in response:
                item = response['Item']
                if item and item['password'] == request.form['password']:
                        rand = os.urandom(6)
                        rand = base64.b64encode(rand).decode('utf-8')
                        sessions.put_item(
                                Item={'sid': rand,
                                      'username':request.form['username']})
                        return redirect(url_for('user', sid = rand,
                                username=request.form['username'],
                        ))
        return redirect(url_for('home'))


@app.route('/user/<username>/<sid>', methods=['GET'])
def user(username, sid):
        response = sessions.get_item(Key={'sid':sid})
        if 'Item' in response:
                item = response['Item']
                if item and item['username'] == username:
                        response = users.get_item(Key={'username': username})
                        item=response['Item']
                        return render_template('user.html',
                                        sid = sid,
                                        username = username,
                                containers=json.loads(item['containers']),
				networks=json.loads(item['networks']))
        return redirect(url_for('home'))

@app.route('/logout/<sid>', methods=['POST'])
def logout(sid):
        #not secure b/c anyone can get logged out by someone
        response = sessions.delete_item(Key={'sid':sid})
        return redirect(url_for('home'))

@app.route('/register', methods=['GET','POST'])
def register():
        if request.method == 'GET':
                return render_template("register.html")
        else:
                username = request.form['username']
                password = request.form['password']
                response = users.get_item(Key={'username':username})
                if 'Item' not in response:
                        users.put_item(Item={
                                'username':username,
                                'password':password,
                                'nextid': '0',
                                'containers': "{}",
				'networks': "{}"})
                        return redirect(url_for('home'))
                else:
                        return redirect(url_for('register'))
                
@app.route('/remove/container/<username>/<sid>', methods=['POST'])
def removecontainer(username,sid):
        id = request.form['id']
        response = users.get_item(Key={'username':username})
        if 'Item' in response:
                item = response['Item']
                containers = json.loads(item['containers'])
		
		#create containter
		resp = lmbd.invoke(
			FunctionName='remove-container',
			Payload=json.dumps({"Id": "a"+id})	
			)
		#if failure do not update
		if resp == "Failure":
                	return redirect(url_for('user', username=username, sid=sid))

                del containers[id]
                users.update_item(Key={
                        'username':username
                },UpdateExpression='SET containers = :c',
                ExpressionAttributeValues={
                        ':c':json.dumps(containers),
                })
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))

@app.route('/remove/network/<username>/<sid>', methods=['POST'])
def removenetwork(username,sid):
        id = str(request.form['id'])
        response = users.get_item(Key={'username':username})
        if 'Item' in response:
                item = response['Item']
                networks = json.loads(item['networks'])
		
		#create containter
		resp = lmbd.invoke(
			FunctionName='remove-network',
			Payload=json.dumps({"Network": networks[id]})	
			)
		#if failure do not update
		if resp == "Failure":
                	return redirect(url_for('user', username=username, sid=sid))

                del networks[id]
                users.update_item(Key={
                        'username':username
                },UpdateExpression='SET networks = :n',
                ExpressionAttributeValues={
                        ':n':json.dumps(networks),
                })
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))

@app.route('/add/container/<username>/<sid>', methods=['POST'])
def addcontainer(username,sid):
        global next_port
	response = users.get_item(Key={'username':username})
        if 'Item' in response:
                item = response['Item']
		containers = json.loads(item['containers'])
                next_id = int(item['nextid'])
                #lambda stuff here eventually
                containers[str(next_id)] = \
                "http://ec2-18-206-154-250.compute-1.amazonaws.com:" + str(next_port)
		
		#create containter
		resp = lmbd.invoke(
			FunctionName='create-container',
			Payload=json.dumps({"User":username, 
				 	    "Id": "a"+str(next_id),
				    	    "Port":str(next_port)})	
			)
		#if failure do not update
		if resp == "Failure":
                	return redirect(url_for('user', username=username, sid=sid))
			
		next_port += 1

                users.update_item(Key={
                        'username':username
                },UpdateExpression='SET containers = :c, nextid = :i',
                ExpressionAttributeValues={
                        ':c':json.dumps(containers),
                        ':i':(next_id+1)
                })
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))

@app.route('/add/network/<username>/<sid>', methods=['POST'])
def addnetwork(username,sid):
	response = users.get_item(Key={'username':username})
	name = request.form['network']
	if name == '':
                return redirect(url_for('user', username=username, sid=sid))
		
        if 'Item' in response:
                item = response['Item']
		networks = json.loads(item['networks'])
                global next_net

		#new net name
                networks[str(next_net)] = name
		
		#create containter
		resp = lmbd.invoke(
			  FunctionName='create-network',
			  Payload=json.dumps({"Network": name,
					      "Netmask": "10.0."+str(next_net)})	
			)
		#if failure do not update
		if resp == "Failure":
                	return redirect(url_for('user', username=username, sid=sid))
			
		next_net += 1

                users.update_item(Key={
                        'username':username
                },UpdateExpression='SET networks = :n',
                ExpressionAttributeValues={
                        ':n':json.dumps(networks),
                })
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))

@app.route('/add/network/container/<username>/<sid>', methods=['POST'])
def addcontainertonetwork(username,sid):
	response = users.get_item(Key={'username':username})
	net = request.form['Network']
	con = request.form['Container']
	if net == '' or con == '':
                return redirect(url_for('user', username=username, sid=sid))
		
        if 'Item' in response:
		networks = json.loads(response['Item']['networks'])
		#add containter to network
		resp = lmbd.invoke(
			  FunctionName='add-container-to-network',
			  Payload=json.dumps({"Network": networks[net],
					      "Container": "a"+con})	
			)
		print(resp)
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))

@app.route('/remove/network/container/<username>/<sid>', methods=['POST'])
def removecontainerfromnetwork(username,sid):
	response = users.get_item(Key={'username':username})
	net = request.form['Network']
	con = request.form['Container']
	if net == '' or con == '':
                return redirect(url_for('user', username=username, sid=sid))
		
        if 'Item' in response:
		networks = json.loads(response['Item']['networks'])
		#add containter to network
		resp = lmbd.invoke(
			  FunctionName='remove-container-from-network',
			  Payload=json.dumps({"Network": networks[net],
					      "Container": "a"+con})	
			)
		print(resp)
                return redirect(url_for('user', username=username, sid=sid))
                
        return redirect(url_for('home'))

#need this
if __name__ == '__main__':
        app.run(debug=True, host='0.0.0.0', port=80)
