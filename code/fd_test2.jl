using LinearAlgebra, Statistics

function nw_weights(theta, Y, H)
    T = size(Y, 1)
    K = zeros(T)
    for t in 1:T
        diff = Y[t, :] - theta
        K[t] = exp(-0.5 * dot(diff, inv(H) * diff))
    end
    s = sum(K)
    return K ./ s
end

function expected_y(theta, Y, H)
    w = nw_weights(theta, Y, H)
    T = size(Y, 1)
    ey = zeros(2)
    for t in 1:T
        ey .+= w[t] * Y[t, :]
    end
    return ey
end

function grad_p_t(theta, Y, H, t)
    w = nw_weights(theta, Y, H)
    ey = expected_y(theta, Y, H)
    return w[t] * inv(H) * (Y[t, :] - ey)
end

function fd_grad_p_t(theta, Y, H, t)
    eps = 1e-7
    grad = zeros(2)
    for i in 1:2
        theta_plus = copy(theta)
        theta_plus[i] += eps
        w_plus = nw_weights(theta_plus, Y, H)[t]
        
        theta_minus = copy(theta)
        theta_minus[i] -= eps
        w_minus = nw_weights(theta_minus, Y, H)[t]
        
        grad[i] = (w_plus - w_minus) / (2 * eps)
    end
    return grad
end

# Test
T = 100
Y = randn(T, 2)
H = [1.0 0.2; 0.2 1.0]
theta = [0.0, 0.0]

for t in 1:min(5, T)
    g_ana = grad_p_t(theta, Y, H, t)
    g_fd = fd_grad_p_t(theta, Y, H, t)
    println("t = $t")
    println("Analytical: ", g_ana)
    println("Finite Diff:", g_fd)
    println("Error:      ", norm(g_ana - g_fd))
end
