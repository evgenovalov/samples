<template>
  <div class="autocomplete">
    <AppInput
      :value="value"
      show-clear-button
      show-cancel-button
      :type="type"
      :placeholder="placeholder"
      :autofocus="autofocus"
      :icon="icon"
      class="autocomplete__input"
      @keydown-enter="onKeydownEnter"
      @input="onInput"
      @cancel="$emit('cancel')"
      @focus="onFocus"
    />
    <transition name="fade">
      <Dropdown
        v-if="isDropdownEnabled && count > 0"
        :items="items"
        :search-phrase="value"
        class="autocomplete__dropdown"
        @select="onSelect"
      />
    </transition>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { Component, Model, Prop, Watch } from 'nuxt-property-decorator'
import { IDropdownItem } from '~/types/IDropdownItem'

@Component({
  name: 'Autocomplete'
})
export default class Autocomplete extends Vue {
  @Prop({
    type: Array,
    required: true
  })
  items!: IDropdownItem[]

  @Prop({
    type: String,
    required: false,
    default: 'text',
    validator(type: any): boolean {
      return ['text', 'email', 'password'].includes(type)
    }
  })
  type!: string

  @Prop({
    type: String,
    required: false,
    default: ''
  })
  placeholder!: string

  @Prop({
    type: String,
    required: false,
    default: ''
  })
  icon!: string

  @Prop({
    type: Boolean,
    required: false,
    default: false
  })
  autofocus!: boolean

  @Model('input', { type: String, required: true })
  value!: string

  isDropdownEnabled: boolean = true

  @Watch('value')
  onValueChanged() {
    this.isDropdownEnabled = true
  }

  onSelect(payload: any) {
    this.isDropdownEnabled = false
    this.$emit('select', payload)
  }

  onInput(value: string) {
    this.$emit('input', value)
  }

  onFocus() {
    this.isDropdownEnabled = true
    this.$emit('focus')
  }

  onKeydownEnter(value: string) {
    this.$emit('keydown-enter', value)
    this.isDropdownEnabled = false
  }

  get count(): number {
    return this.items.length
  }
}
</script>

<style lang="scss" scoped>
.autocomplete {
  position: relative;

  &__dropdown {
    position: absolute;
    top: 50px;
    left: 0;
    right: 0;
  }
}
</style>
