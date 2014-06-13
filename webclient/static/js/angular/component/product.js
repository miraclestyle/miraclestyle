MainApp.factory('Product', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	 
    	var kind = '38';
    	
    	var make_scope = function ()
    	{
    
	       return {
	        	 'form_info' : {'action' : Endpoint.url},
	        	 'accordions' : {
	        	 	'general' : true,
	        	 	'instances' : false,
	        	 },
	        	 'gridConfig' : function (scope)
	            	{
	            		return {
	            			margin : 10
	            		};
	             },
	        	 'completed' : function (data)
	        	 {
	        	 	var ent = (this.options['entity_reader'] ? this.options['entity_reader'](this, data) : data['entity']);
	        	 	this.entity.images.extend(ent['images']);
	        	 },
	        	'pre_save' : function ()
	        	{
	        		var that = this;
	        		var new_order = [];
	        		angular.forEach(this.entity.images, function (item, index) {
	        			new_order.push(item.image);
	        		});
	        		this.entity.sort_images = new_order;
	        	},
	            'removeImage' : function (image)
	        	 {
	        	 	this.entity.images.remove(image);
	        	 },
	        	 'removeContent' : function (content) {
	        	 	this.entity.contents.remove(content);
	        	 },
	        	 'removeVariant' : function (variant)
	        	 {
	        	 	this.entity.variants.remove(variant);
	        	 },
	        	 'manageContent' : function (content) { 
	        	 	
	        	 	var that = this;
	        	 	 
	        	 	var modalInstance = $modal.open({
	                        templateUrl: logic_template('product/manage_content.html'),
	                        controller: function ($scope, $modalInstance, RuleEngine) {
	 
	                            $scope.content = angular.copy(content ? content : {});
	                      
	                            var new_content = content ? false : true;
	             
	                            $scope.save = function () {
	           
	                                 if (new_content)
	                                 {
	                                 	that.entity.contents.push($scope.content);
	                                 }
	                                 else
	                                 {
	                                 	update(content, $scope.content);
	                                 }
	                                 
	                                 $scope.cancel();
	                            };
	
	                            $scope.cancel = function () {
	                                $modalInstance.dismiss('cancel');
	                            };
	
	                        }
	                    });
	        	 	
	        	  },
	        	 'manageVariant' : function (variant) {
	        	 	
	        	 	var that = this;
	        	 	 
	        	 	var modalInstance = $modal.open({
	                        templateUrl: logic_template('product/manage_variant.html'),
	                        controller: function ($scope, $modalInstance, RuleEngine) {
	 
	                            $scope.variant = angular.copy(variant ? variant : {});
	          
	                            if ($scope.variant && ('options' in $scope.variant))
	                            {
	                            	$scope.variant._options = $scope.variant.options.join("\n");
	                            }
	                   
	                            var new_variant = variant ? false : true;
	                   
	                            $scope.save = function () {
	                            	
	                            	 if (!this.variant._options) this.variant._options = '';
	                            	 
	                            	 this.variant.options = this.variant._options.split("\n");
	                            	  
	                                 if (new_variant)
	                                 {
	                                 	that.entity.variants.push(this.variant);
	                                 }
	                                 else
	                                 {
	                                 	update(variant, this.variant);
	                                 }
	                                 
	                                 $scope.cancel();
	                            };
	
	                            $scope.cancel = function () {
	                                $modalInstance.dismiss('cancel');
	                            };
	
	                        }
	                    });
	        	 	
	        	  },
	        	  'removeInstance' : function (instance)
	        	  {
	        	  	
	        	  	  var that = this;
	        	  	  instance.parent = that.entity.key;
	        	  	  
	        	  	  EntityEditor.remove({
	        	  	  	kind : that.entity.kind,
	        	  	  	entity : instance,
	        	  	  	action : 'instance_delete',
	        	  	  	complete : function (entity)
	        	  	  	{
	        	  	  		that.entity._instances.remove(instance);
	        	  	  	}
	        	  	  });
	        	  },
 
	        	  'manageInstance' : function (instance, create)
	        	  {
	        	  	    var that = this;
	        	  	    
	        	  	    if (!instance) instance = {'images' : [], 'contents' : []};
	          
	        	  	    var cfg = {
		                	 'kind' : '38',
		                	 'action' : 'instance_update',
		                	 'action2' : 'instance_read',
		                	 'create_action' : 'instance_create',
		                	 'create_action2' : 'instance_prepare',
		                	 'close' : false,
		                	 'entity_reader' : function($scope, data)
		        		  	 {
		         
		        		  	 	var ent = data['entity'];
		        		  	 	var res = (ent['_instance'] ? ent['_instance'] : instance);
		        		  	 	res._field_permissions = ent['_field_permissions']['_instance'];
		        		  	 	res._action_permissions = ent['_action_permissions'];
		        		  	 	res.kind = ent['kind'];
		        		  		return res;
		        		  	 },
		                	 'entity' : instance,
		                	 'scope' : angular.extend(make_scope(), {}),
		                	 'handle' : function (data)
					         { 
					         	
					 
					            this.uploadConfig = {
					            	'args' : {
					            		'parent' : that.entity.catalog_key,
					            		'action_model' : '38',
					            	}
					            };
					            
					            if (create)
					            {
					            	
	                            	this.entity.variant_signature = create['variant_signature'];
		                            this.entity.parent = create['parent'];
					            }
					            else
					            {
					            	 
					            }
					             
					            
					         },
		                	 'templateUrl' : logic_template('product/manage_instance.html'),
		                 
		               };
	        	  	    
	        		  if (create) {
	        		  	
	        		  	that.entity._instance = {'images' : [], 'contents' : []};
	        		  	cfg['data'] = {'entity' : that.entity};
	        		  	cfg['args'] = create;
	        		  	cfg['complete'] = function (entity)
	        		  	{
	        		  		angular.forEach(that.entity._instances, function (e) {
	        		  			if (e.key == entity.key)
	        		  			{
	        		  				 create = false;
	        		  			}
	        		  		});
	        		  		
	        		  	    if (create)
	        		  	    {
	        		  	    	that.entity._instances.push(entity);
	        		  	    }
	        		  		
	        		  	};
	        		  	EntityEditor.create(cfg);
	        		  }
	        		  else
	        		  {
	        		  	instance['parent'] = that.entity.key;
	        		  	
	        		  	cfg['close'] = true;
	 
	        		  	cfg['args'] = {'variant_signature' : instance['variant_signature'], 'parent' : instance['parent']};
	        		  	EntityEditor.update(cfg);
	        		  }
	        	  },
	        	  'newInstance' : function ()
	        	  {
	        	  	
					var that = this;
	        	 	 
	        	 	var modalInstance = $modal.open({
	                        templateUrl: logic_template('product/create_instance.html'),
	                        controller: function ($scope, $modalInstance, RuleEngine) {
	  							
	  							$scope.variants = [];
	  				 
	  							angular.forEach(that.entity.variants, function (v) {
	 
	  								$scope.variants.push({
	  									'name' : v.name,
	  									'options' : v.options,
	  									'option' : null,
	  								});
	  							});
	  							
	                            $scope.save = function () {
	                            	 
	                            	 var variant_signature = [];
	                            	 angular.forEach($scope.variants, function (v) {
	                            	 	var d = {};
	                            	 	d[v.name] = v.option;
	                            	 	variant_signature.push(d);
	                            	 });
	                            	 
	                            	 var parent = that.entity.key;
	                            	 
	                            	 Endpoint.post('instance_read', '38', {
	                            	 	'variant_signature' : variant_signature,
	                            	 	'parent' : parent,
	                            	 }).success(function (data) {
	                            	 	
	                            	 	if (!data['entity']['_instance'])
	                            	 	{ 
		                            	 	that.manageInstance(false, {'variant_signature' : variant_signature, 'parent' : parent});
	                            	 	}
	                            	 	else
	                            	 	{
	                            	 		that.manageInstance(data.entity._instance);
	                            	 	}
	                            	 	 
	                            	 	$scope.cancel();
	                            	 	
	                            	 });
	                            	 
	                            };
	
	                            $scope.cancel = function () {
	                                $modalInstance.dismiss('cancel');
	                            };
	
	                        }
	                    });
	        	  }, 
	        	 _do_user_admin : function (entity, action) {
	        	 	
	        	 	    var that = this;

                        var handle = function () {

                            var modalInstance = $modal.open({
                                templateUrl: logic_template('product/user_admin.html'),
                                windowClass: 'modal-medium',
                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                              

                                    $scope.rule = that.rule;
                                    $scope.action = action;
                                    $scope.log = {
                                        'message': '',
                                        'key': that.entity['key'],
                                        'state' : that.entity['state'],
                                        'note' : '',
                                    };

                                    $scope.save = function () {

                                        Endpoint.post(action, that.entity['kind'], $scope.log)
                                            .success(function (data) {

                                                EntityEditor.update_entity(that, data, ['_images']);

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

                    },
                    
                    duplicate : function()
                    {
                    	this._do_user_admin(this.entity, 'duplicate');
                    },
	      		 
	      		
	    	};
    	
    			
    	};
    	  
    	
        return {
 
            create: function (catalog_key, complete) {
              
               return EntityEditor.create({
               		 'close' : false,
                	 'kind' : kind,
                	 'entity' : {},
                	 'scope' : make_scope(),
                	 'handle' : function (data)
			         {
			            this.entity['parent'] = catalog_key;
			            this.entity.catalog_key = catalog_key;
			            
			            this.uploadConfig = {
			            	'args' : {
			            		'parent' : catalog_key,
			            	}
			            };
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('product/manage.html'),
                	 'args' : {
                	 	'parent' : catalog_key,
                	 }
                });
                
            },
            update: function (catalog_key, entity, complete)
            {
             
                return EntityEditor.update({
                	 'kind' : kind,
                	 'entity' : entity,
                	 'scope' : make_scope(),
                	 'handle' : function (data)
			         {
			            this.update_mode = true;
			            this.entity.catalog_key = catalog_key;
			            
			            this.uploadConfig = {
			            	'args' : {
			            		'parent' : catalog_key,
			            	}
			            };
			            
			            var ref = this;
			      
		                if (!ref.live_entity._instances.length)
		                {
		        
		                	Endpoint.post('read_instances', '38', ref.live_entity).success(function (data) {
		       
			                	ref.live_entity._instances = ref.entity._instances = data.entity._instances;
			                	
			                });
		                }
		                
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('product/manage.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);