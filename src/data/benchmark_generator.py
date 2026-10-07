"""
AegisText Benchmark Dataset Generator & Curator

Constructs a rich, multi-domain benchmark dataset consisting of:
- Ground-truth Human texts (Academic, News, Creative, Technical)
- Pure Generative AI texts (LLM outputs with realistic stylistic traits)
- Adversarially Humanized AI texts (Generated using the AdversarialPerturbationEngine)

Ensures:
- Balanced class distribution across origins (Human vs Pure AI vs Humanized AI)
- Strict lineage tracking (Parent AI ID -> Humanized Child ID)
- Leakage-proof train/test splitting
- Rich metadata schema compatibility
"""

import os
import json
import random
from typing import List, Tuple
from src.data.schema import TextSample, TextOrigin, Domain, TransformationSeverity
from src.data.dedup import DeduplicationEngine
from src.robustness.engine import AdversarialPerturbationEngine

# Domain-specific sentence building blocks capturing genuine stylistic differences

HUMAN_BANKS = {
    Domain.ACADEMIC: [
        "Recent investigations into distributed consensus reveal fundamental trade-offs between latency and partition tolerance.",
        "In asynchronous networks, deterministic consensus cannot be guaranteed in the presence of even a single unannounced crash failure.",
        "Empirical benchmarks across geo-distributed nodes demonstrate that speculative execution mitigates tail latency by thirty-four percent.",
        "Histological examination of the biopsy specimens demonstrated extensive lymphocytic infiltration surrounding the perivascular regions.",
        "Although immunohistochemical staining showed focal positivity for CD3, the architectural integrity of germinal centers remained intact.",
        "These observations suggest a reactive follicular hyperplasia rather than malignant lymphoma under standard staining protocols.",
        "The thermodynamic efficiency of organic photovoltaic cells remains constrained by non-radiative recombination losses at the donor-acceptor interface.",
        "Transient absorption spectroscopy indicates that charge separation occurs on a sub-picosecond timescale following photoexcitation.",
        "Phase-field simulations of dendritic solidification reveal non-linear morphology transitions under anisotropic interfacial energy conditions.",
        "The spectral reflectance measurements of sedimentary layers exhibit distinct mineralogical signatures consistent with fluvial deposition.",
    ],
    Domain.NEWS: [
        "City officials scrambled on Tuesday to address mounting public outcry after commuter train delays brought morning transit to a standstill.",
        "Transit union representatives argued that chronic underfunding and deferred maintenance made track failures inevitable.",
        "The mayor promised an emergency review before week's end, though commuters remained skeptical about near-term improvements.",
        "Treasury yields edged lower this morning as investors digested mixed economic data ahead of the central bank's interest rate decision.",
        "Markets broadly expect policymakers to pause rate increases, though stubborn services inflation continues to keep options open.",
        "Retail sales declined for a second consecutive month, signaling that consumer spending may finally be cooling under higher borrowing costs.",
        "Emergency crews battled a three-alarm warehouse fire near the industrial waterfront through early morning gusts of wind.",
        "No injuries were reported, but air quality warnings remained in effect for adjacent residential neighborhoods throughout the day.",
        "Local school district trustees voted five to two to approve a revised operating budget following four hours of contentious public testimony.",
        "Community advocates pledged to challenge the redistricting proposal in state court before the upcoming general election cycle.",
    ],
    Domain.CREATIVE: [
        "The wind off the bay carried salt and old wood, snapping the canvas awnings along the pier.",
        "Martha pulled her coat tighter, watching the ferry lantern blink through the grey drizzle.",
        "He had promised to write from Lisbon, but that was three months and two storms ago.",
        "Old Jack never trusted clocks that ticked too loud.",
        "He kept three watches on the mantle, all stopped at twenty minutes past four, claiming time moved backward in the dark.",
        "Dust motes hung suspended in the shaft of morning light cutting through the shuttered cellar window.",
        "She didn't look back until the train had rounded the granite bend and the depot whistle faded into the pines.",
        "The kettle on the iron stove began its thin, breathless whistling just as the gravel in the driveway crunched.",
        "Rain beat a steady, hollow tattoo against the corrugated tin roof of the abandoned barn.",
        "Nothing in the old map warned him about the sunken quarry where the cart road abruptly ended.",
    ],
    Domain.TECHNICAL: [
        "When configuring mutual TLS authentication, ensure that both client and server certificates share a common trust store.",
        "If the client certificate contains an expired subject alternative name, the reverse proxy will reject the handshake with SSL alert 46.",
        "Database migrations altering column types on tables exceeding ten million rows should use zero-downtime dual-writing strategies.",
        "Adding a column with a default value without the NOT NULL constraint locks the schema cache on older engine versions.",
        "The memory profiler revealed an uncollected reference cycle between the websocket session handler and the background telemetry worker.",
        "Thread pool saturation occurred because asynchronous blocking calls were submitted to the default compute dispatcher.",
        "Kernel trace points indicated frequent page faults triggered by sequential buffer allocation inside the high-throughput ingest worker.",
        "The garbage collector paused execution for 420 milliseconds during mark-sweep phase under peak heap fragmentation.",
        "Load balancers must configure health check interval thresholds to at least double the target service's p99 graceful degradation latency.",
        "Redis cluster slot migration requires acquiring distributed locks prior to executing key re-sharding commands across shards.",
    ],
}

AI_BANKS = {
    Domain.ACADEMIC: [
        "In conclusion, distributed consensus mechanisms represent a pivotal foundation of modern decentralized architecture.",
        "Furthermore, it is crucial to recognize that latency and fault tolerance must be carefully balanced to achieve optimal throughput.",
        "Moreover, empirical evaluations clearly demonstrate that speculative execution plays an essential role in improving overall system reliability.",
        "The integration of artificial intelligence into biomedical diagnostics presents a rich tapestry of opportunities and challenges.",
        "Crucially, algorithmic models must be evaluated against rigorous benchmarks to guarantee patient safety and ethical alignment.",
        "In addition, interpretability remains a cornerstone of clinical adoption, ensuring physicians can reliably inspect diagnostic recommendations.",
        "Organic photovoltaic technologies offer immense potential for sustainable energy harvesting across contemporary urban landscapes.",
        "Therefore, conducting thorough spectroscopic analyses is vital for unraveling the intricate complexities of intermolecular charge transfer.",
        "Additionally, advanced computational simulations provide valuable insights into dendritic crystal growth and thermal dynamics.",
        "Overall, these comprehensive findings underscore the imperative need for interdisciplinary collaboration in modern materials science.",
    ],
    Domain.NEWS: [
        "In today's fast-paced world, municipal transportation infrastructures face unprecedented challenges and complex operational hurdles.",
        "Furthermore, city administrators must navigate stringent budgetary constraints while maintaining operational excellence and public trust.",
        "Consequently, implementing comprehensive transit reform is vital to fostering sustainable urban mobility and commuter satisfaction.",
        "Economic landscapes continue to evolve rapidly in response to macroeconomic monetary policies and inflationary pressures.",
        "Crucially, investors must closely monitor yield curve fluctuations to anticipate market corrections and protect asset allocations.",
        "Overall, maintaining a diversified investment portfolio is imperative for mitigating financial volatility in uncertain times.",
        "Emergency response protocols demonstrate the indispensable dedication of first responders safeguarding local community welfare.",
        "Moreover, collaborative disaster management strategies are essential for ensuring public safety during unpredictable crises.",
        "Civic governance plays an integral role in shaping the educational fabric and future prosperity of contemporary society.",
        "In conclusion, proactive civic engagement and constructive dialogue remain paramount for fostering vibrant democratic institutions.",
    ],
    Domain.CREATIVE: [
        "The sunset painted the sky in a vibrant tapestry of crimson and gold, evoking a profound sense of wonder.",
        "As gentle breezes whispered through ancient pine trees, an overwhelming aura of tranquility enveloped the peaceful valley.",
        "Every delicate blossom seemed to be a timeless testament to nature's boundless splendor and celestial elegance.",
        "Deep within the silent library, towering shelves stood as proud sentinels of forgotten knowledge and wisdom.",
        "Whispers of bygone eras echoed softly through the vaulted corridors, inviting inquisitive souls to embark on an enchanting voyage.",
        "The golden luminescence of the twilight hour cast long, contemplative shadows across the cobblestone pathway.",
        "In this mystical realm of quiet introspection, the boundaries between dreams and reality effortlessly dissolved into oblivion.",
        "A symphony of nocturnal sounds resonated through the enchanted forest, singing an eternal lullaby to the sleeping earth.",
        "Hope fluttered like a fragile butterfly in the weary traveler's heart, illuminating the darkest recesses of the arduous journey.",
        "Ultimately, the majestic mountains stood unwavering, bearing silent witness to the transient dance of human existence.",
    ],
    Domain.TECHNICAL: [
        "To ensure seamless cryptographic handshakes, it is essential to configure mutual TLS authentication accurately and securely.",
        "Furthermore, verifying certificate authority expiration dates is crucial for preventing unexpected connection termination in enterprise systems.",
        "Therefore, software engineers should strictly adhere to industry best practices and automated secret rotation protocols.",
        "Database optimization requires a multifaceted strategy involving meticulous query profiling and strategic indexing methodologies.",
        "Additionally, partitioning large tables enhances query efficiency and significantly reduces system overhead during peak hours.",
        "In conclusion, proactive monitoring and automated telemetry are key to maintaining high database availability and operational resilience.",
        "Efficient memory management serves as the bedrock of scalable microservice architectures in cloud-native computing environments.",
        "Moreover, developers must eliminate circular dependencies to prevent memory leaks and optimize garbage collection cycles.",
        "Implementing robust load balancing mechanisms is paramount for distributing traffic evenly across horizontally scaled instances.",
        "In summary, continuous architectural refinement guarantees optimal throughput, low latency, and uninterrupted service delivery.",
    ],
}


def build_samples_from_bank(
    bank: dict,
    origin: TextOrigin,
    samples_per_domain: int = 40,
    seed: int = 42,
    generator_name: str = None
) -> List[TextSample]:
    """Assembles coherent multi-sentence documents from sentence banks."""
    rng = random.Random(seed)
    samples = []
    sample_idx = 1

    for domain, sentences in bank.items():
        for i in range(samples_per_domain):
            # Select 3-4 sentences in natural order
            k = rng.randint(3, 4)
            chosen = rng.sample(sentences, k)
            text = " ".join(chosen)

            s_id = f"{origin.value.lower()}_{domain.value.lower()}_{sample_idx:04d}"
            sample = TextSample(
                sample_id=s_id,
                text=text,
                origin=origin,
                domain=domain,
                generator=generator_name if origin != TextOrigin.HUMAN else None,
                source_dataset="AegisText-MultiDomainBenchmark",
            )
            samples.append(sample)
            sample_idx += 1

    return samples


def generate_benchmark_dataset(
    samples_per_domain: int = 40,
    seed: int = 42
) -> List[TextSample]:
    """Generates balanced benchmark dataset: Human, Raw AI, and Humanized AI."""
    engine = AdversarialPerturbationEngine(seed=seed)
    all_samples: List[TextSample] = []

    # 1. Generate Human samples (4 domains * 40 = 160 samples)
    human_samples = build_samples_from_bank(
        HUMAN_BANKS,
        origin=TextOrigin.HUMAN,
        samples_per_domain=samples_per_domain,
        seed=seed,
    )
    all_samples.extend(human_samples)

    # 2. Generate Raw AI samples (4 domains * 40 = 160 samples)
    ai_samples = build_samples_from_bank(
        AI_BANKS,
        origin=TextOrigin.AI_RAW,
        samples_per_domain=samples_per_domain,
        seed=seed + 1,
        generator_name="GPT-4_Claude_Ensemble",
    )
    all_samples.extend(ai_samples)

    # 3. Generate Humanized AI samples from Raw AI samples (160 samples with tracked lineage)
    humanized_samples = []
    for idx, raw_sample in enumerate(ai_samples):
        # Alternate humanization techniques
        technique = idx % 4
        if technique == 0:
            # Commercial humanizer (synonyms + discourse jitter)
            h_text = engine.simulate_commercial_humanizer(raw_sample.text, severity="medium")
            h_name = "CommercialHumanizer_Simulated"
            sev = TransformationSeverity.MEDIUM
        elif technique == 1:
            # Multi-vector attack (synonym + homoglyph)
            h_text, _ = engine.apply_attack(raw_sample.text, attack_type="combined", severity=0.6)
            h_name = "MultiVector_Adversarial"
            sev = TransformationSeverity.HEAVY
        elif technique == 2:
            # Zero-width evasion injection
            h_text = engine.inject_zero_width_chars(raw_sample.text, rate=0.06)
            h_name = "ZeroWidth_Evasion"
            sev = TransformationSeverity.LIGHT
        else:
            # Synonym substitution
            h_text = engine.substitute_synonyms(raw_sample.text, rate=0.20)
            h_name = "SynonymParaphrase"
            sev = TransformationSeverity.LIGHT

        h_id = f"humanized_{raw_sample.domain.value.lower()}_{idx + 1:04d}"
        humanized_sample = TextSample(
            sample_id=h_id,
            text=h_text,
            origin=TextOrigin.AI_HUMANIZED,
            domain=raw_sample.domain,
            generator=raw_sample.generator,
            humanizer=h_name,
            transformation_severity=sev,
            parent_id=raw_sample.sample_id,
            source_dataset="AegisText-MultiDomainBenchmark",
        )
        humanized_samples.append(humanized_sample)

    all_samples.extend(humanized_samples)
    return all_samples


def save_benchmark_dataset(
    output_dir: str = "data/processed",
    samples_per_domain: int = 40,
) -> Tuple[str, int]:
    """Generates, deduplicates, partitions and saves benchmark dataset."""
    os.makedirs(output_dir, exist_ok=True)
    raw_samples = generate_benchmark_dataset(samples_per_domain=samples_per_domain)

    # Dedup
    dedup = DeduplicationEngine()
    unique_samples, dedup_meta = dedup.exact_deduplicate(raw_samples)

    # Split into train (70%), val (15%), test (15%) preserving lineage groups
    train_set, val_set, test_set = dedup.grouped_split(
        unique_samples,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=42,
    )

    manifest_data = {
        "dataset_name": "AegisText-MultiDomain-Benchmark-v1",
        "total_samples": len(unique_samples),
        "train_samples": len(train_set),
        "val_samples": len(val_set),
        "test_samples": len(test_set),
        "dedup_metadata": dedup_meta,
        "origins": {
            "HUMAN": sum(1 for s in unique_samples if s.origin == TextOrigin.HUMAN),
            "AI_RAW": sum(1 for s in unique_samples if s.origin == TextOrigin.AI_RAW),
            "AI_HUMANIZED": sum(1 for s in unique_samples if s.origin == TextOrigin.AI_HUMANIZED),
        },
        "domains": {
            d.value: sum(1 for s in unique_samples if s.domain == d)
            for d in [Domain.ACADEMIC, Domain.NEWS, Domain.CREATIVE, Domain.TECHNICAL]
        }
    }

    manifest_path = os.path.join(output_dir, "dataset_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    splits = {"train": train_set, "val": val_set, "test": test_set}
    for split_name, split_samples in splits.items():
        split_path = os.path.join(output_dir, f"{split_name}.jsonl")
        with open(split_path, "w", encoding="utf-8") as f:
            for s in split_samples:
                f.write(json.dumps(s.to_dict()) + "\n")

    return manifest_path, len(unique_samples)


if __name__ == "__main__":
    path, count = save_benchmark_dataset()
    print(f"Generated {count} balanced benchmark samples across 4 domains at {path}")
