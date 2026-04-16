// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MealWindowCard from './MealWindowCard.vue'

describe('MealWindowCard', () => {
  it('renders bounded evidence wording from the migrated profile', () => {
    const wrapper = mount(MealWindowCard)

    expect(wrapper.text()).toContain('associated with better glucose and blood-pressure markers')
    expect(wrapper.text()).toContain('General TRF guidance for adults')
  })
})
