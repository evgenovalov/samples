<template>
  <div
    class="carousel"
    :class="{ 'carousel--with-dots': showDots }"
  >
    <div
      ref="roll"
      class="carousel__scroll"
    >
      <slot />
      <div class="carousel__gap" />
    </div>
    <div
      v-if="showDots"
      class="carousel__dots"
    >
      <span
        v-for="i in Object.keys(statuses)"
        :key="i"
        class="carousel__dot"
        :class="{ 'carousel__dot--active': statuses[i]}"
      />
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue'
import { Component, Prop, Watch } from 'nuxt-property-decorator'

@Component({
  name: 'Carousel'
})
export default class Carousel extends Vue {
  @Prop({ type: Boolean, required: false, default: true })
  showDots!: boolean

  @Prop({ type: String, required: false })
  scrollTo!: string

  mutationObserver!: MutationObserver
  intersectionObserver!: IntersectionObserver
  statuses = {}
  elementIndices: { [key: string]: number } = {}

  onSlotsChanged() {
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect()
    }
    const roll = this.$refs.roll as Element
    for (let i = 0; i < roll.children.length - 1; i++) {
      const slide = roll.children.item(i) as Element
      const slideId = slide.getAttribute('data-slide-id')
      if (!slideId) {
        throw new Error('Please provide unique "data-slide-id" attribute for all slides')
      }
      this.elementIndices[slideId] = i
      this.intersectionObserver.observe(slide)
    }
  }

  observerCallback(entries: IntersectionObserverEntry[]) {
    entries.forEach((entry) => {
      const slideIndex: number = this.elementIndices[entry.target.getAttribute('data-slide-id') as string]
      if (entry.intersectionRatio >= 0.5) {
        this.$set(this.statuses, slideIndex, true)
      } else {
        this.$set(this.statuses, slideIndex, false)
      }
    })
    this.$emit('change', this.statuses)
  }

  mounted() {
    if (this.showDots) {
      this.connect()
      this.onSlotsChanged()
    }
    /*
    * We need to start to show slides even if some slides in loading status (async data with v-if=false).
    * We're waiting for 300ms, then scroll the roll to start position.
    * It's required bcs the rendering order is random here.
    * If new slides will appear, we'll stop at previous roll position – bcs user probably is started to interact.
    */
    this.initScroll()
  }

  @Watch('scrollTo')
  initScroll() {
    if (this.scrollTo) {
      this.scrollToAnchor()
    } else {
      this.scrollToStart()
    }
  }

  scrollToAnchor() {
    const roll = this.$refs.roll as HTMLDivElement
    const slideId = this.scrollTo.replace(/#reactive\d+/gm, '')
    const target = roll.querySelector(`[data-slide-id="${slideId}"]`) as HTMLDivElement
    if (target) {
      roll.scrollTo({ left: target.offsetLeft - 20, behavior: 'smooth' })
    } else {
      this.scrollToStart()
    }
  }

  scrollToStart() {
    const roll = this.$refs.roll as Element
    if (roll) {
      roll.scrollTo({ left: 0, behavior: 'smooth' })
    }
  }

  connect() {
    this.mutationObserver = new MutationObserver(this.onSlotsChanged)
    this.mutationObserver.observe(this.$refs.roll as Element, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true
    })
    this.intersectionObserver = new IntersectionObserver(this.observerCallback, {
      root: this.$refs.roll as Element,
      threshold: 0.5
    })
  }

  disconnect() {
    if (this.intersectionObserver) {
      this.intersectionObserver.disconnect()
    }
    if (this.mutationObserver) {
      this.mutationObserver.disconnect()
    }
  }

  beforeDestroy() {
    this.disconnect()
  }
}
</script>

<style lang="scss" scoped>
@import '~assets/scss/_vars';

.carousel {
  position: relative;
  margin: 0 -20px;

  &--with-dots &__scroll {
    padding-bottom: 56px;
  }

  &__scroll {
    display: flex;
    overflow-x: scroll;
    padding: 12px 20px 32px;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    /* For Firefox */
    scrollbar-width: none;

    &::-webkit-scrollbar {
      /* For WebKit */
      display: none;
    }
  }

  &__gap {
    margin-right: -20px;
    scroll-snap-align: end;
    min-width: 20px;
  }

  &__dots {
    position: absolute;
    left: 0;
    bottom: 32px;
    width: 100%;
    display: flex;
    justify-content: center;
  }

  &__dot {
    display: inline-block;
    background: #AFB3BF;
    width: 8px;
    height: 8px;
    border-radius: 4px;
    margin-right: 8px;
    transition: background 150ms ease-in-out;

    &:last-child {
      margin-right: 0;
    }

    &--active {
      background: $color-primary;
    }
  }
}
</style>

<!-- Global styles for nested slides -->
<style lang="scss">
.carousel {

  &__scroll > * {
    width: 100%;
    margin: 0 8px 0 0;
    scroll-margin-left: 20px;
    scroll-snap-margin-left: 20px;
    scroll-snap-align: start;
    scroll-snap-stop: always;

    &:nth-last-child(2) {
      margin-right: 0;
    }
  }
}
</style>
