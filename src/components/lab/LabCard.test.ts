// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LabCard from './LabCard.vue'

describe('LabCard', () => {
  it('shows evidence by default when an evidence slot is present', () => {
    const wrapper = mount(LabCard, {
      props: {
        label: 'TEST CARD',
        title: 'Test Title',
        accent: '#00D4AA',
        citation: 'Test Citation',
        hasOutput: true,
      },
      slots: {
        inputs: '<div class="inputs">Inputs</div>',
        output: '<div class="output">Output</div>',
        evidence: '<div class="evidence">Evidence body</div>',
      },
    })

    expect(wrapper.find('.lab-card__evidence-wrap').exists()).toBe(true)
    expect(wrapper.find('.lab-card__evidence-wrap').classes()).toContain('lab-card__evidence-wrap--open')
    expect(wrapper.find('.lab-card__evidence-toggle').attributes('aria-expanded')).toBe('true')
    expect(wrapper.text()).toContain('Evidence body')
  })
})
