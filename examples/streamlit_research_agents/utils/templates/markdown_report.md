# {{ title }}
{% if subtitle %}
## {{ subtitle }}
{% endif %}

**Generated:** {{ generated_date }}
{% if processing_time %}
**Processing Time:** {{ processing_time }}
{% endif %}

---

## Executive Summary

{{ executive_summary }}

## Research Question

{{ research_question }}

## Methodology

{{ methodology }}

## Key Findings

{% for finding in findings %}
### {{ finding.title if finding.title else "Finding " + loop.index|string }}

{{ finding.content }}

{% endfor %}

## Conclusions

{{ conclusions }}

## Recommendations

{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}

## Sources

{% for source in sources %}
- {{ source }}
{% endfor %}

{% if appendices %}
## Appendices

{% for appendix in appendices %}
### {{ appendix.title }}

{{ appendix.content }}

{% endfor %}
{% endif %}

---

{% if agents_used %}
*This report was generated using the following AI agents: {{ agents_used|join(', ') }}*
{% endif %}
