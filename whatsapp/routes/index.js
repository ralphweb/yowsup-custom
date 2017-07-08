var express = require('express');
var router = express.Router();
var MongoClient = require('mongodb').MongoClient;

var url = 'mongodb://localhost:27017/whatsapp';

var hashtags,total,campaign;

/* GET home page. */
MongoClient.connect(url, function(err, db) {
	console.log("connected to MongoDB");
	router.get('/', function(req, res, next) {
	  hashtags = [];
	  total = 0;
	  getCountMongo(req,res,next);
	});

	router.get('/:campaign', function(req, res, next) {
	  hashtags = [];
	  total = 0;
	  getCountMongo(req,res,next);
	});

	var getCountMongo = function(req,res,next) {
		var topics = db.collection('topics');
		var campaigndb = db.collection('campaign');
		var mustArr = {};

		if(req.params.campaign) {
			mustArr["token"] = req.params.campaign;
		}

		campaigndb.find(mustArr).toArray(function(error, items) {
			if(items.length>0) {
				//Existe campaña
				campaign = items.pop();
				topics.find({active:true}).toArray(function(error, items) {
					items.forEach(function(topic) {
						console.log(topic.hash);
						hashtags.push({topic:topic.hash,count:0});
					});
					getCountRecursive(res,0);
				});
			} else {
				//No existe campaña
				res.send({ "error":"no hay campañas creadas"});
			}
		});
	}

	var getCountRecursive = function(res,index) {
		if(index<hashtags.length) {
			var topic = hashtags[index];
			var messages = db.collection('messages');
			messages.count({"$and":[{"vote":true},{"topic":topic.topic},{"campaign":campaign.token}]},function(error, count) {
				topic.count = count;
				total += count;
				hashtags[index] = topic;
				getCountRecursive(res,index+1);
			});
		} else {
			calculatePercentages(res)
		}
	}

	var calculatePercentages = function(res) {
		var index = 0;
		var result = {};
		hashtags.forEach(function(hashtag){
			var elm = hashtag;
			elm.percentage = (elm.count/total*100).toFixed(2);
			hashtags[index] = elm;
			index++;
		});

		var messages = db.collection('messages');
		messages.count({},function(error, count) {
			result.campaign = campaign.name;
			result.token = campaign.token;
			result.status = campaign.active?'Abierta':'Cerrada';
			result.total = count;
			result.votes = total;
			result.topics = hashtags.sort(function(a, b) {
			    return parseInt(b.count) - parseInt(a.count);
			});
			res.send(result);
		});
	}
});

module.exports = router;
