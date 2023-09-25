import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#-----------------------------------------------------------------------------------------------------------------------------
# Part 1 - Building a Blockchain
class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, pre_hash = '0')
        self.nodes = set()
        
    def create_block(self, proof, pre_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'pre_hash': pre_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_pre_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, pre_proof):
        new_proof = 1
        check_proof = False
        while check_proof == False:
            hash_operation = hashlib.sha256(str(new_proof**2-pre_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
                
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def valid_check(self, chain):
        check_block = {
            'valid': True,
            'fail_index': -1
        }
        index = 1
        pre_block = chain[0]
        while check_block['valid'] == True and index < len(chain):
            block = chain[index]
            proof = block['proof']
            pre_proof = pre_block['proof']
            hash_operation = hashlib.sha256(str(proof**2-pre_proof**2).encode()).hexdigest()

            if block['pre_hash'] != self.hash(pre_block) or hash_operation[:4] != '0000':
                check_block['valid'] = False
                check_block['fail_index'] = index

            index += 1
            pre_block = block      
        return check_block
    
    def add_transaction(self, sender, receiver, amount):
        new_transaction = {
            'sender':sender,
            'receiver':receiver,
            'amount':amount}
        self.transactions.append(new_transaction)
        
        pre_block = self.get_pre_block()
        return pre_block['index'] + 1
    
    def add_node(self, address_node):
        parsed_url = urlparse(address_node)
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        network = self.nodes
        max_length = len(self.chain)
        length_of_node = 0
        response = None
        longest_chain = None
        chain = None
        
        for node in network:
            response = requests.get(f'http://{node}/get_blockchain')
            if response.status_code == 200:
                length_of_node = response.json()['length']
                chain = response.json()['chain']           
                if length_of_node > max_length and self.valid_check(chain):
                    max_length = length_of_node
                    longest_chain = chain             
        
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False
            
        

#-----------------------------------------------------------------------------------------------------------------------------
# Part 2 - Mining blockchain

# Creat a Web App
app = Flask(__name__)

# Creat a Blockchain
blockchain = Blockchain()

# Creating an address for the node on Port
node_address = str(uuid4()).replace('-','')

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    pre_block = blockchain.get_pre_block()
    pre_proof = pre_block['proof']
    proof = blockchain.proof_of_work(pre_proof)
    pre_hash = blockchain.hash(pre_block)
    
    blockchain.add_transaction(node_address, 'TuanMinh', 100)
    block = blockchain.create_block(proof,pre_hash)

    response ={
        'message': 'Congratulations, you just mined a block!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'pre_hash': block['pre_hash'],
        'transactions': block['transactions']
    }

    return jsonify(response), 200

# Getting full blockchain
@app.route('/get_blockchain', methods = ['GET'])
def get_blockchain():
    response ={
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }

    return jsonify(response), 200

# Check Blockchain is valid?
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    check_valid = blockchain.valid_check(blockchain.chain)
    if check_valid['valid'] == True:
        response = {
            'message': 'The blockchain is valid!'
        }
    else:
        response = {
            'message': 'The blockchain is not valid.......!',
            'fail_index': check_valid['fail_index']
        }

    return jsonify(response), 200

# Adding new transaction to the blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_key = ['sender','receiver','amount']
    if not all (key in json for key in transaction_key):
        return 'Some elements of the transaction are missing', 400

    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {
        'message': f'This transaction is added in block {index}'
        }
    return jsonify(response), 201


#-----------------------------------------------------------------------------------------------------------------------------
# Part 3 - Decentralizing our blockchain

# Connect new nodes 
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes == None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)

    response = {'message': 'Add nodes successfull. All of nodes:',
                'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

# Replace the chain by longest chain
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    check_replace_chain = blockchain.replace_chain()
    if check_replace_chain:
        response = {
            'message': 'The blockchain is replaced by the logest chain!',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'The blockchain is the longest chain!',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

# Running app
app.run(host = '0.0.0.0', port = 5001)

#-----------------------------------------------------------------------------------------------------------------------------


