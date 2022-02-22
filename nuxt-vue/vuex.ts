import { Module, Action, Mutation, VuexModule } from 'vuex-module-decorators'
import { AxiosResponse } from 'axios'
import { IProfile } from '~/types/IProfile'
import { IJWT } from '~/types/IJWT'
import { parseJWT } from '~/utils/jwt'
import { IAuthCredentials } from '~/types/IAuthCredentials'
import { $axios, $apollo } from '~/utils/api'
import { IUser } from '~/types/generated'
import { ISignUpForm } from '~/types/ISignUpForm'
import { ISignInForm } from '~/types/ISignInForm'
import userGQL from '~/apollo/queries/profile/user.gql'
import updateUserGQL from '~/apollo/mutations/profile/update-user.gql'
import updateAvatarGQL from '~/apollo/mutations/profile/update-avatar.gql'
import updatePasswordGQL from '~/apollo/mutations/profile/update-password.gql'
import { uploadImage } from '~/utils/image-upload'
import { toBase64 } from '~/utils/atob'

@Module({
  name: 'profile',
  namespaced: true,
  stateFactory: true,
  preserveState: true
})
export default class Profile extends VuexModule {
  userProfile: IProfile = {
    credentials: null,
    user: null
  }

  _refreshTokenPromise: Promise<AxiosResponse<IAuthCredentials>> | null = null
  _logoutPromise: Promise<AxiosResponse> | null = null

  get jwt(): IJWT | null {
    if (!this.userProfile.credentials?.accessToken) {
      return null
    }
    return parseJWT(this.userProfile.credentials.accessToken)
  }

  get authorized(): boolean {
    return !!this.userProfile.credentials?.accessToken
  }

  get profile(): IProfile {
    return this.userProfile
  }

  get credentials(): IAuthCredentials | null {
    return this.userProfile.credentials
  }

  get user(): IUser | null {
    return this.userProfile.user
  }

  get refreshTokenPromise(): Promise<AxiosResponse<IAuthCredentials>> | null {
    return this._refreshTokenPromise
  }

  get logoutPromise(): Promise<AxiosResponse> | null {
    return this._logoutPromise
  }

  @Mutation
  setCredentials(credentials: IAuthCredentials | null) {
    this.userProfile.credentials = credentials
  }

  @Mutation
  setUser(user: IUser | null) {
    this.userProfile.user = user
  }

  @Mutation
  setRefreshTokenPromise(promise: Promise<AxiosResponse<IAuthCredentials>> | null) {
    this._refreshTokenPromise = promise
  }

  @Mutation
  setLogoutPromise(promise: Promise<AxiosResponse> | null) {
    this._logoutPromise = promise
  }

  @Action({ rawError: true })
  async signUp(form: ISignUpForm) {
    const { data: tokens }: { data: IAuthCredentials } = await $axios
      .post<IAuthCredentials>('/auth/register', form)
    this.setCredentials(tokens)
    await this.fetchMe()
  }

  @Action({ rawError: true })
  async signIn(form: ISignInForm) {
    const { data: tokens }: { data: IAuthCredentials } = await $axios
      .post<IAuthCredentials>('/auth/login', form)
    this.setCredentials(tokens)
    await this.fetchMe()
  }

  @Action({ rawError: true })
  async fetchMe() {
    const response = await $apollo.query<{ user: IUser }>({ query: userGQL })
    this.setUser(response.data.user)
  }

  @Action({ rawError: true })
  async updateProfile(user: Partial<IUser>) {
    const response = await $apollo.mutate<{ user: IUser }>({
      mutation: updateUserGQL,
      variables: { ...user }
    })
    if (response.data?.user) {
      this.setUser(response.data.user)
    }
  }

  @Action({ rawError: true })
  async updateAvatar(imgFile: File) {
    const media = await uploadImage(imgFile, this.user?.username)
    const response = await $apollo.mutate<{ user: IUser }>({
      mutation: updateAvatarGQL,
      variables: {
        imageId: media.id
      }
    })
    if (response.data?.user) {
      this.setUser(response.data.user)
    }
  }

  @Action({ rawError: true })
  async updatePassword({
    newPassword,
    oldPassword,
    userId
  }: {
    newPassword: string
    oldPassword: string
    userId: string
  }) {
    return await $apollo.mutate({
      mutation: updatePasswordGQL,
      variables: {
        newPassword,
        oldPassword,
        userId
      }
    })
  }

  @Action({ rawError: true })
  async refreshToken() {
    try {
      if (!this.refreshTokenPromise) {
        this.setRefreshTokenPromise(
          $axios
            .post<IAuthCredentials>('/auth/refresh', {
              refreshToken: this.credentials?.refreshToken
            }, { params: { bypassAuthorization: true } })
        )
      }
      const response = (await this.refreshTokenPromise) as AxiosResponse<IAuthCredentials>
      this.setRefreshTokenPromise(null)
      this.setCredentials(response.data)
      return response.data
    } catch (e) {
      this.setRefreshTokenPromise(null)
      this.unsetData()
      return e
    }
  }

  @Action({ rawError: true })
  unsetData() {
    this.setCredentials(null)
    this.setUser(null)
  }

  @Action({ rawError: true })
  async logout() {
    if (process.server) {
      this.unsetData()
      return
    }

    if (this.logoutPromise) {
      // log-outing
      await this.logoutPromise
    } else {
      this.setLogoutPromise(
        $axios
          .post('/auth/logout', { deviceToken: toBase64(navigator.userAgent) })
          .finally(() => this.unsetData())
      )
    }
    this.setLogoutPromise(null)
  }
}
