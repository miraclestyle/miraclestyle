var useinit = function (key, fun)
{
	if (initdata[key])
	{
		var initdata2 = {};
		
		angular.copy(initdata, initdata2);
		 
		delete initdata;
	 
		return initdata2;
		
	}
	else
	{
	    var call = fun;
	    
	    if (angular.isFunction(fun))
	    {
	    	call = fun();
	    }
		 
		return call;
	}
	
};

var handle_few_datatypes = function (response)
{
 
  	 	var formatter = {'created' : Date, 'updated' : Date, 'logged' : Date};
  	 	 
  	 	var do_format = function (entity) {
  	 				
			if (angular.isObject(entity))
			{
				angular.forEach(entity, function (value, key) {
					if (key in formatter)
					{
						entity[key] = new formatter[key](value);
						
					}
				 
				});
			}
			
  	 	};
  	 	// this is probably just temporary because we will need more robust transformer
  	 	if (angular.isObject(response))
  	 	{
 
  	 		if ('entities' in response)
  	 		{ 
  	 			angular.forEach(response.entities, do_format);
 
  	 		}
  	 		
  	 		if ('entity' in response)
  	 		{ 
  	 			do_format(response.entity);
 
  	 		}
  	 		 
  	 	}
  	 	 
  	 	return response;
};

handle_few_datatypes({'entity' : current_user});
handle_few_datatypes({'entity' : initdata});

angular.module('app.ui',
	  [
	   'app.ui.transition',
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.select2',
	  ]
);

var MainApp = angular.module('MainApp', ['ui.router', 'ngBusy', 'ngSanitize', 'ngUpload', 'ngStorage', 'checklist-model', 'app.ui'])
.config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {
  	 
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
     $httpProvider.defaults.transformResponse.push(handle_few_datatypes);
 
     $locationProvider.hashPrefix('!');
     
	 $locationProvider.html5Mode(true);
     
}])
.factory('RuleEngine', function () {
	
	function RuleEngine(data)
	{
		var that = this;
		
		this.executable = {};
		this.required = {};
	    this.invisible = {};
		this.writable = {};
		this.arguments = {};
		
		this._action_permission_translate = function (action_name)
		{
			return this._rule_action_permissions[this._rule_actions[action_name]['key']];
		};
 
		this._check_field = function (name, what)
	    {
	    	return this._rule_field_permissions[name][what];
	    };
	    
		this._writable = function (name)
	    {
	    	return this._check_field(name, 'writable');
	    };
	    
		this._invisible = function (name)
	    {
	    	return this._check_field(name, 'invisible');
	    };
	    
		this._required = function (name)
	    {
	    	return this._check_field(name, 'required');
	    };
		
		this._executable = function (action_name)
	    {
	    	var gets = this._action_permission_translate(action_name);
	    	
	    	return gets['executable'];
	    };		
		
		this.init = function ()
		{
	        angular.forEach(this._rule_actions, function (value, key) {
		    	that.executable[key] = that._executable(key);
		    	
		    	angular.forEach(value.arguments, function (argument_value, argument_key) {
		    		if (!that.arguments[key]) that.arguments[key] = {};
		    		
		    		that.arguments[key][argument_key] = argument_value;
		    	});
		    	
		    });
		    
		    angular.forEach(this._rule_field_permissions, function (value, key) {
		    	
		    	that.required[key] = that._required(key);
		    	that.writable[key] = that._writable(key);
		    	that.invisible[key] = that._invisible(key);
		    	
		    });
	    };
		
		this.update = function (info)
	    {
	    	
	    	if (!info['entity'] || !info['entity']['_action_permissions'])
	    	{
	    		return;
	    	}
			
			this._rule = info['entity'];
			this._rule_action_permissions = this._rule['_action_permissions'];
			this._rule_field_permissions = this._rule['_field_permissions'];
			this._rule_actions = this._rule['_actions'];
			 
			this.init();
			
			
			 
		};
	
		if ((data && data['entity'] && data['entity']['_action_permissions']))
		{
			
			this.update(data);
	    }

		      
		}
  
	
	return {
		factory : function (data) {
			return new RuleEngine(data);
		}
	};
	  
})
.factory('Confirm', ['$modal', function ($modal) {
	
    var Confirm = function(options)
    {
    	 if (!options) options = {};
    	 
    	 var defaults = {
    	 	text : {
    	 		Yes : 'Yes',
    	 		No : 'No',
    	 	},
    	 	message : 'Are you sure you want to proceed with this action?',
    	 	templateUrl : logic_template('opt/misc', 'basic_confirm.html'),
    	 	windowClass : 'modal-small',
    	 	controller: function ($scope, $modalInstance) {
						  
				  $scope.data = options;
 
 				  $scope.yes = function (){
 				  	$modalInstance.dismiss('Yes');
 				  };
 				  
				  $scope.no = function () {
				    $modalInstance.dismiss('No');
				  };
			},
			
			callbacks : {Yes : angular.noop, No : angular.noop}
    	 	
    	 };
    	 
    	 options = angular.extend(defaults, options);
    	 
    	 var modalInstance = $modal.open(options);
    	  
    	 modalInstance.result.then(function close(what) {
 
		   }, function dismiss(what) {
 
			    if (angular.isFunction(options['callbacks'][what])) options['callbacks'][what]();
		   });
    };
	
	return {
		notice : function (message, ok, options)
		{
			var defaults = {
				message : message,
				callbacks : {
					Yes : ok,
				},
				text : {
					Yes : 'Ok',
				}
			};
			
			options = angular.extend(defaults, options);
			
			Confirm(options);
		},
		sure : function (yes, no, options) {
			
			var defaults = {
				message : 'Are you sure you want to proceed with this action?',
				callbacks : {
					Yes : ok,
					No : no,
				},
				text : {
					Yes : 'Yes',
					No : 'No',
				}
			};
			
			options = angular.extend(defaults, options);
			
			Confirm(options);
			
		},
		error500 : function (output, options)
		{
			var defaults = {
				message : output,
				templateUrl : logic_template('opt/misc', 'error500.html'),
				text : {
					Yes : 'Close',
				}
			};
			
			options = angular.extend(defaults, options);
			
			Confirm(options);
		},
		
		action_denied : function (output, options)
		{
			var defaults = {
				message : 'You do not have permission to perform this action.',
				templateUrl : logic_template('opt/misc', 'action_denied.html'),
				text : {
					Yes : 'Ok',
				}
			};
			
			options = angular.extend(defaults, options);
			
			Confirm(options);
		},
		
		changes : function (ok, no, options) {
			
			var defaults = {
				message : 'Do you want to save your changes before leaving?',
				callbacks : {
					Yes : ok,
					No : no,
				},
				text : {
					Yes : 'Yes',
					No : 'No',
				}
			};
			
			options = angular.extend(defaults, options);
			
			Confirm(options);
		},
		
	};
}])
.factory('Endpoint', ['$http', function ($http) {
	
	
	var endpoint_url = '/endpoint';
	
	var _compile = function(action, model, data, config)
	{
		 if (!config) config = {};
			
		 return [angular.extend({
				action_model : model,
				action_key : action,
			}, data), config];
		
	};
	
	return {
		url : endpoint_url,
		post : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
			
			return $http.post(endpoint_url, compiled[0], compiled[1]);
		},
		get : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
		    
		    compiled[1]['params'] = $.param(compiled[0]);
			
			return $http.get(endpoint_url, compiled[1]);
		},
	};
}])
.factory('Title', ['$rootScope', function ($rootScope) {
	
	var suffix = 'MIRACLESTYLE', titles = [];
 
	$rootScope.pageTitle = '';
	
	_compile = function (title_to_compile)
	{
		title_to_compile.unshift(suffix);
		title_to_compile.reverse();
		return title_to_compile.join('-');
	};
	
	return {
		set : function (title)
		{
		   $rootScope.pageTitle = title + ' - ' + suffix;
		   
		   return this;
		},
		append : function (title) {
			
		   if (angular.isArray(title))
		   {
		   	  angular.forEach(title, function (a) {
		   	  	  titles.push(a);
		   	  });
		   }
		   else
		   {
		   	  titles.push(title);
		   } 	
		   
		   
		   $rootScope.pageTitle = _compile(titles);	
		   
		   return this;
			
		},
		prepend : function () {
			
		   if (angular.isArray(title))
		   {
		   	  angular.forEach(title, function (a) {
		   	  	  titles.unshift(a);
		   	  });
		   }
		   else
		   {
		   	  titles.unshift(title);
		   } 	
			
			$rootScope.pageTitle = _compile(titles);	
			
			return this;
		},
		reset : function()
		{
			titles = [];
			
			$rootScope.pageTitle = _compile(titles);
			
			return this;
		}
	};
}])
.controller('HandleLog', ['$scope', 'Endpoint', function ($scope, Endpoint) {
 
    $scope.logs = -1;
	$scope.commander = {'isOpen' : false, 'loading' : false};
	 
	 
	var load_more = function (that)
	{
		
		if ($scope.logs != -1)
		{
			if (!$scope.commander.loading && $scope.history.args.more)
			{
				$scope.commander.loading = true;
				
				Endpoint.post('history', $scope.history.model, $scope.history.args).success(function (data) {
					
				 
					angular.forEach(data.entities, function (value) {
					     $scope.logs.push(value);
					});
 
					$scope.history.args.next_cursor = data.next_cursor;
					$scope.history.args.more = data.more;
					
					$scope.commander.loading = false;
				});		
				
			}
		}		
		
	};
	 
	$scope.$on('scrollEnd', function (that) {
 		load_more(that);
	});
	
	$scope.$watch('commander.isOpen', function (isOpen) {
 
		if (isOpen && $scope.logs == -1)
		{
			Endpoint.post('history', $scope.history.model, $scope.history.args).success(function (data) {
			 
				$scope.logs = data.entities;
				$scope.history.args.next_cursor = data.next_cursor;
				$scope.history.args.more = data.more;
			});
		}  
	});
}])
.run(['$rootScope', '$state', 'Title', function ($rootScope, $state, Title) {
    
    $rootScope.current_user = current_user;
    $rootScope.$state = $state;
    $rootScope.ui_template = ui_template;
    $rootScope.logic_template = logic_template;
    $rootScope.DATE_FULL = "yyyy-MM-dd HH:mm:ss Z";
  
}]);