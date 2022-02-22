import { NuxtAxiosInstance } from '@nuxtjs/axios'
import { AxiosError, AxiosRequestConfig } from 'axios'
import { userProfile } from '~/store'
import { $axios } from '~/utils/api'
import { isTokenExpired } from '~/utils/auth'

/*
* This interceptor checks when user token is already expired and sends a request for token updating
* All requests will be paused until a server sends a new pair of access and refresh tokens
*/

async function requestInterceptor(request: AxiosRequestConfig) {
    // refresh token if it's expired already AND there is no active refreshing
    if (userProfile.authorized && isTokenExpired(userProfile.jwt) && !userProfile.refreshTokenPromise) {
        userProfile.refreshToken()
    }

    // all requests are waiting here; but refresh request bypass this
    if (userProfile.refreshTokenPromise && !request.url?.includes('/refresh')) {
        await userProfile.refreshTokenPromise
    }

    // set authorization headers if required
    if (userProfile.authorized && !request?.params?.bypassAuthorization) {
        request.headers.Authorization = `Bearer ${userProfile.credentials?.accessToken}`
    } else {
        // remove 'bypassAuthorization' param (uses only for frontend checking)
        request.params && delete request.params.bypassAuthorization
        request.headers && delete request.headers.Authorization
    }

    return request
}

async function errorResponseInterceptor(error: AxiosError) {
    if ((error.response?.status !== 401 && error.response?.status !== 403)) {
        // no access error -> reject other requests here
        return Promise.reject(error)
    }

    if (userProfile.authorized && !userProfile.refreshTokenPromise) {
        userProfile.refreshToken()
    }

    try {
        await userProfile.refreshTokenPromise
    } catch {
        return Promise.reject(error)
    }

    // retry; new token will be attached in the REQUEST interceptor
    return $axios(error.config)
}

// redirect (can be added)
export default function ({ $axios }: { $axios: NuxtAxiosInstance }) {
    $axios.interceptors.request.use(requestInterceptor)
    $axios.interceptors.response.use(undefined, errorResponseInterceptor)
}
