SEARCH_KIND_CONFIG = {
	'61': {
    	'title' : 'Templates',
    	'add_new' : 'New Template',
    	'service' : 'Notify',
    	'fields' : [{
			        'label': 'Name',
			        'key': 'name'
		  		    }, 
		  		    {
			        'label': 'Active',
				    'key': 'active'
				    }]
    },
    '38': {
    	'title' : 'Product Templates',
    	'add_new' : 'New Product Template',
    	'service' : 'Product',
    	'fields' : [{
			        'label': 'Name',
			        'key': 'name'
		  		    }, 
		  		    {
			        'label': 'Description',
				    'key': 'description',
				    },
				    {
			        'label': 'Code',
				    'key': 'code',
				    }]
    },
    '62': {
    	'title' : 'Widgets',
    	'add_new' : 'New Widget',
    	'service' : 'Nav',
    	'fields' : [{
			        'label': 'Name',
			        'key': 'name'
		  		    }, 
		  		    {
			        'label': 'Active',
				    'key': 'active'
				    }]
    },
   '60': {
    	'title' : 'Roles',
    	'add_new' : 'New Role',
    	'service' : 'AppRole',
    	'fields' : [{
			        'label': 'Name',
			        'key': 'name'
		  		    }, 
		  		    {
			        'label': 'Active',
				    'key': 'active'
				    }]
    },
    '35': {
    	'title' : 'Catalogs',
    	'add_new' : 'New Catalog',
    	'service' : 'Catalog',
    	'fields' : [{
			        'label': 'Name',
			        'key': 'name'
		  		    }, 
		  		    {
			        'label': 'State',
				    'key': 'state',
				    },
				    {
			        'label': 'Created',
				    'key': 'created',
				    }]
    },
   '8': {
    	'title' : 'Users',
    	'add_new' : 'New User',
    	'service' : 'AppUser',
    	'fields' : [{
			        'label': 'Name',
			        'key': 'name'
		  		    }, 
		  		    {
			        'label': 'State',
				    'key': 'state'
				    }]
    },
    
    '49': {
        'title' : 'Journals',
        'add_new' : 'New Journal',
        'service' : 'Journal',
        'fields' : [{
                    'label': 'Name',
                    'key': 'name'
                    }, 
                    {
                    'label': 'Created',
                    'key': 'created'
                    },
                    {
                    'label': 'State',
                    'key': 'state'
                    }]
    },
    
   '47': {
        'title' : 'Category',
        'add_new' : 'New Category',
        'service' : 'Category',
        'fields' : [{
                    'label': 'Name',
                    'key': 'complete_name'
                    }, 
                    {
                    'label': 'Created',
                    'key': 'created'
                    },
                    {
                    'label': 'Active',
                    'key': 'active'
                    }]
    },
    
    
    'default': {
    	'title' : 'No data specified for this kind',
    	'add_new' : 'N/A',
    	'service' : '',
    	'fields' : []
    },
};
MainApp.factory('App', ['$rootScope', '$http', '$location', '$modal', 'Endpoint', 'Title',

    function ($rootScope, $http, $location, $modal, Endpoint, Title) {

        return {
            search: function (args, config) {
                return Endpoint.post('read_domains', '0', args, config);
            },
            sudo_search: function (args, config) {
                return Endpoint.post('sudo_search', '6', args, config);
            },
            create: function () {
                var that = this;

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('app/create.html'),
                        controller: function ($scope, $modalInstance, RuleEngine, Confirm) {

                            $scope.rule = RuleEngine.factory(data['entity']);
                            $scope.entity = data['entity'];
                            $scope.step = 1;
                            $scope.form_info = {'action' : Endpoint.url};
                            
                            $scope.createUploadUrlOnSelectOptions = {
                            	'complete' : function (data)
	                            {
	                            	$scope.form_info.action = data.upload_url;
	                            }
                            };
                   
                            $scope.nextStep = function (which_step) {
                                $scope.step = which_step;
                            };

                            $scope.completed = function (data) {
                                if(data['entity']) {

                                    Confirm.notice('Your app is now in process of creation, you will recieve an e-mail as soon as the application is created.',
                                        function () {
                                            $scope.cancel();
                                        });
                                        
                                } else {

                                    Confirm.notice('An error occurred, please try again.', function () {
                                        Endpoint.post('prepare', '6', {
                                            'upload_url': Endpoint.url
                                        }).success(function (data) {
                                            $scope.form_info.action = data.upload_url;
                                        });
                                    });

                                }

                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };

                Endpoint.post('prepare', '6', {}).success(handle);

            },
            update: function (entity) {
                var that = this;

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('app/update.html'),
                        controller: function ($scope, $modalInstance, RuleEngine, Select2Options) {

                            update(entity, data['entity']);
							
							$scope.form_info = {'action' : Endpoint.url, 'blobstore' : false};
                            $scope.rule = RuleEngine.factory(data['entity']);
                            $scope.entity = angular.copy(entity);
                            $scope.container = {};
                            $scope.history = {
                                'kind': entity['kind'],
                                'args': {
                                    'key': entity['key'],
                                }
                            };
                            
                            $scope.select2_domain_user = Select2Options.factory({
					   			kind : '8',
					   			args_callback : function (element, args)
						   	    {
						   				args['domain'] = $scope.entity.key;
						   	    }
					   	    });
 
                           
                            $scope.createUploadUrlOnSelectOptions = {
                            	'complete' : function (data)
	                            {
	                            	$scope.form_info.action = data.upload_url;
	                            }
                            };

                            $parentScope = $scope;

                            $scope.sudo = function () {
                                var handle = function () {

                                    var modalInstance = $modal.open({
                                        templateUrl: logic_template('admin/sudo.html'),
                                        windowClass: 'modal-medium',
                                        controller: function ($scope, $modalInstance, RuleEngine) {

                                            $scope.rule = $parentScope.rule;
                                            $scope.log = {
                                                'message': '',
                                                'note': '',
                                                'state': $parentScope.entity['state'],
                                                'key': $parentScope.entity['key'],
                                            };

                                            $scope.save = function () {

                                                Endpoint.post('sudo', '6', $scope.log)
                                                    .success(function (data) {

                                                        update($parentScope.entity, entity, data['entity']);

                                                        $scope.rule.update(data['entity']);

                                                        $scope.cancel();

                                                    });

                                            };

                                            $scope.cancel = function () {
                                                $modalInstance.dismiss();
                                            };
                                        }
                                    });

                                };

                                handle();
                            };

                            $scope._do_user_admin = function (entity, action) {

                                var handle = function () {

                                    var modalInstance = $modal.open({
                                        templateUrl: logic_template('app/user_admin.html'),
                                        windowClass: 'modal-medium',
                                        controller: function ($scope, $modalInstance, RuleEngine, $timeout) {

                                            $scope.rule = $parentScope.rule;
                                            $scope.action = action;
                                            $scope.log = {
                                                'message': '',
                                                'key': $parentScope.entity['key'],
                                            };

                                            $scope.save = function () {

                                                Endpoint.post(action, '6', $scope.log)
                                                    .success(function (data) {

                                                        update($parentScope.entity, entity, data['entity']);

                                                        $scope.rule.update(data['entity']);

                                                        $scope.cancel();

                                                    });

                                            };

                                            $scope.cancel = function () {
                                                $modalInstance.dismiss();
                                            };
                                        }
                                    });

                                };

                                handle();

                            };

                            $scope.suspend = function () {
                                this._do_user_admin(entity, 'suspend');
                            };

                            $scope.activate = function () {
                                this._do_user_admin(entity, 'activate');
                            };
                            
                            var saved = function (data) {
                       
                                  update($scope.entity, entity, data['entity']);

                                  $scope.rule.update(data['entity']);

                            };
                            
                            $scope.completed = function (data)
                            {
                            	saved(data);
                            	 
                            };

                            $scope.save = function () {

                                Endpoint.post('update', '6', {
                                    'name': $scope.entity['name'],
                                    'primary_contact': $scope.entity['primary_contact'],
                                    'key': $scope.entity['key'],
                                })
                                .success(saved);

                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };

                Endpoint.post('read', '6', {
                    'key': entity['key']
                }).success(handle);

            }

        };

    }
])
    .controller('AppView', ['$scope', '$stateParams', '$rootScope', '$state',
        function ($scope, $stateParams, $rootScope, $state) {
	 
            var nav = $rootScope.nav;
            var menu = null;
            angular.forEach(nav.menu, function (value) {
            	if (!value.search_form && !menu)
            	{
            		menu = value;
            	}
            });
            
            if (menu)
            {
            	 var menu = menu['filters'][0];
	             var params = {
	                'domain_key': nav.domain.key,
	                'kind': menu['model'],
	                'query': JSON.stringify(menu['query'])
	            };
	  
	            $state.go('app_view_search', params);
            }
           

        }
    ])
    .controller('AppSearch', ['$scope', 'Title', 'Endpoint', '$stateParams', '$rootScope', 'RuleEngine', 'search', '$injector', '$state',
        function ($scope, Title, Endpoint, $stateParams, $rootScope, RuleEngine, search, $injector, $state) {
     
            angular.forEach(search.entities, function (value) {
                value.rule = RuleEngine.factory(value);
            });

            var kind = $stateParams['kind'];
            var config = SEARCH_KIND_CONFIG[kind];
  
            $rootScope.search.doSearch = function ()
            {
         
                var cfg = {
                    'domain_key': $rootScope.nav.domain.key,
                    'kind': this.kind,
                    'query': JSON.stringify({
                        'search' : this.send,
                    })
                };
 
            	$state.go('app_view_search', cfg);
            };
  
            if (!config)
            {
            	config = SEARCH_KIND_CONFIG['default'];
            	var service = undefined;
            }
            else
            {
            	var service = $injector.get(config['service']);
            }

            $scope.search = search;
            $scope.fields = config['fields'];
            $scope.title = config['title'];
            $scope.add_new = config['add_new'];
             
            $scope.removeItem = function (e) {
            	$scope.search.entities.remove(e);
            };
 
            $scope.create = function () {
				service.create($stateParams['domain_key'], function (new_entity) {
					new_entity.rule = RuleEngine.factory(new_entity);
					$scope.search.entities.push(new_entity);
				}, $scope);
            };

            $scope.update = function (entity) {
				service.update(entity, null, $scope);
            };
            
            $scope.remove = function (entity) {
				service.remove(entity, function () {
					    $scope.search.entities.remove(entity);
  					 
				}, $scope);
            };
            
            

        }
    ])
    .controller('AppList', ['$scope', 'App', 'AppUser', 'apps', 'Confirm', 'RuleEngine', 'Title',
        function ($scope, App, AppUser, apps, Confirm, RuleEngine, Title) {

            Title.set('My Apps');
            
            var domains = apps.domains;
            var domain_users = apps.domain_users;

            var entities = [];

            angular.forEach(domains, function (domain, i) {
            	domain.rule = RuleEngine.factory(domain);
            	angular.forEach(domain_users, function (user) {
            		if (user.namespace == domain.key)
            		{
            			domain._domain_user = user;
            			domain._domain_user.rule = RuleEngine.factory(user);
            		}
            		
            	});
 
            	entities.push(domain);
            });
      
   
            $scope.apps = entities;

            $scope.toggleMainMenu(1);
       
            $scope.updateApp = function (app) {
                App.update(app);
            };

            $scope.createApp = function () {
                App.create();
            };
            
            $scope.acceptApp = function (app)
            {
            	 AppUser.accept(app._domain_user.key, function (data) {
            	 	if (data['entity'])
            	 	{
            	 		update(app, data['domain']);
            	 		update(app._domain_user, data['entity']);
            	 		 
            	 		app.rule.update(data['domain']);
            	 		app._domain_user.rule.update(data['entity']);
            	 	}
            	 });
            };
            
            $scope.declineApp = function (app)
            {
            	$scope.removeFromApp(app);
            	
            };
            
            $scope.removeFromApp = function (app)
            {
            	
            	AppUser.remove(app._domain_user, function (data) {
            		if (data['entity'])
            		{ 
            			  entities.remove(app);
            		}
            	});
            	
            };

        }
    ])
    .run(['$rootScope', '$location', 'Account', 'Endpoint',
        function ($rootScope, $location, Account, Endpoint) {

            $rootScope.nav = {};

            $rootScope.doLogin = function () {
                Account.ask_login(function () {
                    $location.path('/');
                });
            };

            $rootScope.doLogout = function () {

                Account.logout(function () {
                    $location.path('/');
                });

            };

        }
    ]);