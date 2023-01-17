shader_type spatial;

//Uniforms controlled by the simulation that will be the same for all spacetime objects.
uniform int observation_mode = 0;
uniform bool doppler = false;
uniform float c = 4.0;
uniform float c_squared = 16.0;
uniform float player_world_time = 0.0;
uniform vec3 player_position = vec3(0.0);
uniform vec3 player_velocity = vec3(0.0);
uniform float player_gamma = 1.0;

//Uniforms that may change on a per-instance basis.
uniform sampler2D texture_albedo;
uniform vec3 direction = vec3(1.0, 0.0, 0.0);

//Returns the object's 3-position as a function of time.
vec3 position_procession(float t) {
	vec3 dir = normalize(direction);
	return dir * sin(0.85 * c * t);
}

//Returns the object's 3-velocity as a function of time.
vec3 velocity_procession(float t) {
	float epsilon = 0.01;
	return (position_procession(t + epsilon) - position_procession(t)) / epsilon;
}

//Returns the lorentz factor of velocity v, by definition.
float lorentz_factor(vec3 v) {
	return 1.0 / sqrt(1.0 - dot(v, v) / c_squared);
}

//Returns the 4-position of an event located at 4-position r4 in some original reference frame,
//as observed by a reference frame moving at v relative to the original frame.
vec4 lorentz_transform(vec3 v, vec4 r4) {
	if (length(v) == 0.0)
		return r4;
	
	float t = r4.w;
	vec3 r = r4.xyz;
	float gamma = lorentz_factor(v);
	vec3 n = normalize(v);
	
	float t_prime = gamma * (t - dot(v, r) / c_squared);
	vec3 r_prime = r + (gamma - 1.0) * dot(n, r) * n - gamma * t * v;
	
	return vec4(r_prime, t_prime);
}

//Returns the result of relativistic velocity addition between v and u.
vec3 velocity_composition(vec3 v, vec3 u) {
	if (length(v) == 0.0)
		return u;
	float gamma = lorentz_factor(v);
	vec3 numerator = u + (gamma - 1.0) * dot(u, v) / dot(v, v) * v + gamma * v;
	float denominator = gamma * (1.0 + dot(u, v) / c_squared);
	return numerator / denominator;
}

//Returns the 4-position at which the given vertex should be observed by the player, given the player's current 4-position/velocity.
//object_origin is the "center" of the object, and local_vert is the displacement between the object's "center" and the vertex in question.
//Note that the object needs to have a defined "center" in order to emulate Born Rigid motion.
vec4 get_observed_r4(vec3 object_origin, vec3 local_vert) {
	
	int max_iter = 100;
	int iter = 0;
	float ct_lower_bound = (player_world_time - 1000.0) * c;
	float ct_upper_bound = (player_world_time + 1000.0) * c;
	float test_ct;
	vec4 test_point;
	float error;
	
	//("World as measured" observation mode)
	//Perform binary search to find the intersection between the player's plane of simultaneity and the vertex's world line.
	if (observation_mode == 0) {
		vec4 simultaneity_plane_origin = vec4(player_position, player_world_time * c);
		vec4 simultaneity_plane_normal = vec4(-player_velocity, c);
		
		while (iter < max_iter) {
			test_ct = (ct_lower_bound + ct_upper_bound) / 2.0;
			vec3 v = velocity_procession(test_ct / c);
			vec4 delta = lorentz_transform(-v, vec4(local_vert, 0.0));
			delta = vec4(delta.xyz, delta.w * c);
			test_point = vec4(object_origin + position_procession(test_ct / c), test_ct) + delta;
			error = dot(simultaneity_plane_normal, test_point - simultaneity_plane_origin);
			if (error == 0.0) {
				return vec4(test_point.xyz, test_point.w / c);
			}
			if (error < 0.0) {
				ct_lower_bound = test_ct;
			} else {
				ct_upper_bound = test_ct;
			}
			iter += 1;
		}
		
	}
	
	//("World as seen" observation mode)
	//Perform binary search to find the intersection between the player's past light cone and the vertex's world line.
	if (observation_mode == 1) {
		vec3 light_cone_origin_space = player_position;
		float light_cone_origin_ct = player_world_time * c;
		vec3 separation_space;
		float separation_ct;
		
		while (iter < max_iter) {
			test_ct = (ct_lower_bound + ct_upper_bound) / 2.0;
			vec3 v = velocity_procession(test_ct / c);
			vec4 delta = lorentz_transform(-v, vec4(local_vert, 0.0));
			delta = vec4(delta.xyz, delta.w * c);
			test_point = vec4(object_origin + position_procession(test_ct / c), test_ct) + delta;
			separation_space = light_cone_origin_space - test_point.xyz;
			separation_ct = light_cone_origin_ct - test_point.w;
			error = dot(separation_space, separation_space) - pow(separation_ct, 2.0);
			if (error == 0.0) {
				return vec4(test_point.xyz, test_point.w / c);
			}
			if (error < 0.0) {
				ct_lower_bound = test_ct;
			} else {
				ct_upper_bound = test_ct;
			}
			iter += 1;
		}
		
	}
	
	return vec4(test_point.xyz, test_point.w / c);
}

//Repositions the vertex to be consistent with relativity, by
//1) Finding the position the vertex would be observed at, given that the speed of light is finite, and
//2) Lorentz transforming the resulting position from world-space to player-space.
void vertex() {
	mat4 INV_WORLD_MATRIX = inverse(WORLD_MATRIX);
	vec3 WORLD_VERTEX = (WORLD_MATRIX * vec4(VERTEX, 1.0)).xyz;
	
	vec4 player_r4 = vec4(player_position, player_world_time);
	vec4 observed_r4 = get_observed_r4(WORLD_VERTEX - VERTEX, VERTEX);
	vec4 spacetime_displacement = lorentz_transform(player_velocity, observed_r4 - player_r4);
	vec3 displacement = spacetime_displacement.xyz;
	
	WORLD_VERTEX = displacement;
	VERTEX = (INV_WORLD_MATRIX * vec4(WORLD_VERTEX, 1.0)).xyz;
	
	if (doppler) {
		vec3 relative_velocity = velocity_composition(-player_velocity, velocity_procession(observed_r4.w));
		if (length(relative_velocity) > 0.0 && length(displacement) > 0.0) {
			float relative_cosine = dot(displacement, relative_velocity) / length(displacement) / length(relative_velocity);
			float doppler_factor = 1.0 / (player_gamma * (1.0 + length(relative_velocity) / c * relative_cosine));
			float mapped_doppler = atan(log(doppler_factor));
			COLOR = vec4(-mapped_doppler, 1.0 - abs(mapped_doppler), mapped_doppler, 1.0);
		}
		else {
			COLOR = vec4(0.0, 1.0, 0.0, 1.0);
		}
	}
	
}

//Only relevant when the doppler effect is turned on. Recolors objects based on whether they are approaching/receding, as per the doppler shift of light.
void fragment() {
	if (doppler)
		ALBEDO = COLOR.rgb;
	else
		ALBEDO = texture(texture_albedo, UV).rgb;
}
