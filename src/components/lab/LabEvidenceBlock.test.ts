// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import LabEvidenceBlock from './LabEvidenceBlock.vue'

describe('LabEvidenceBlock', () => {
  it('renders the normalized evidence profile fields', () => {
    const wrapper = mount(LabEvidenceBlock, {
      props: {
        profile: {
          evidenceTier: 'B',
          effectSummary: 'Controlled breathing sessions can raise rMSSD in adult lab studies.',
          populationSummary: 'Adult lab and meta-analytic breathing studies.',
          mainCaveat: 'Acute response varies by technique, session length, and individual responsiveness.',
          uncertaintyFactors: ['technique', 'session duration', 'baseline state'],
          claimBoundary: 'Session-level HRV guidance for adults, not a personal biometric prediction.',
        },
      },
    })

    expect(wrapper.text()).toContain('Tier B')
    expect(wrapper.text()).toContain('Controlled breathing sessions can raise rMSSD in adult lab studies.')
    expect(wrapper.text()).toContain('Adult lab and meta-analytic breathing studies.')
    expect(wrapper.text()).toContain('Session-level HRV guidance for adults, not a personal biometric prediction.')
  })

  it('does not fabricate tier or boundary from legacy-only props', () => {
    const wrapper = mount(LabEvidenceBlock, {
      props: {
        effect: 'Legacy effect',
        population: 'Legacy population',
        caveat: 'Legacy caveat',
      } as never,
    })

    expect(wrapper.find('.lab-evidence').exists()).toBe(false)
    expect(wrapper.text()).toBe('')
  })
})
